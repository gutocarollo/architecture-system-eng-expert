"""
Unified Super R1 dispatcher — the `/qualify` endpoint's brain.

`qualify()` accepts one structured payload and drives the whole flow.
Flow selection (FBI-2925):

  - service_type == 'consorcio' → consorcio_d0 (always sync)
  - Investimentos + D+1 + allows_d1_batch (100k-300k) → regular_d1
  - else Investimentos → regular_d0 (sync pool pick; includes future dates for
    Advisory2 / Closer / Consultoria)
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import text as sa_text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import GetSettings
from app.core.r1_meeting import MEETING_DURATION
from app.integrations.salesforce_integration import (
    account_has_consorcio_origin,
    execute_r1_from_opportunity_flow,
    execute_r1_resume_converted_lead_flow,
    execute_r1_partial_flow_from_account,
    execute_r1_partial_flow_lead,
    execute_r1_scheduling_flow,
    filter_active_user_ids,
    get_advisor_salesforce_id,
    get_salesforce_connection,
    get_salesforce_connection_as_user,
    is_jwt_flow_configured,
    resolve_sf_user_by_email,
    validate_lead_update_data,
)
from app.repositories.advisor import AdvisorRepository
from app.repositories.routing_failure_repo import RoutingFailureRepository
from app.repositories.routing_repo import (
    RoutingRepository,
    SlotLockHandle,
    _pending_d1_table,
)
from app.schemas.routing import ConfirmRoutingResponse, SelectedAdvisorInfo
from app.schemas.super_r1 import (
    FlowTaken,
    QualifiedAdvisor,
    QualifyRequest,
    QualifyResponse,
)
from app.services.availability_service import verify_slot
from app.services.super_r1_config_service import load_consorcio_config
from app.services.routing_service import RoutingService, get_cluster_weights
from app.services import idempotency_store
from app.services.super_r1_service import (
    CATEGORIA_300K_5M,
    ConsorcioAdvisor,
    ConsorcioPoolResolution,
    PoolSpec,
    allows_d1_batch,
    get_pool_spec,
    resolve_consorcio_pool,
    is_account_id,
    is_d1_or_later,
    patrimony_to_categoria,
)

logger = logging.getLogger(__name__)

# Use the timezone database so historical daylight-saving offsets remain valid.
_SP_TZ = ZoneInfo("America/Sao_Paulo")
_RECOVERY_IDEMPOTENCY_SCOPE = "super_r1_converted_lead_recovery"
_RECOVERY_IDEMPOTENCY_ACTOR = "system@super-r1-recovery"


@dataclass(frozen=True)
class SlotLockAcquisition:
    acquired: bool
    handle: Optional[SlotLockHandle] = None

    def __bool__(self) -> bool:
        return self.acquired


# FBI-2987 item M4 — 409 "escolha outro horário" detail becomes a typed dict
# instead of a bare string.
#
# Why it mattered as measured: the frontend only settles the Idempotency-Key
# on a DEFINITIVE 400/422 and keeps it on 409 (frontend/app/(pages)/super-r1/
# [lead_id]/page.tsx) — by design, so a transient retry doesn't mint a second
# Opportunity. But these particular 409s ask the SDR to change the slot, which
# changes the request payload; resubmitting under the SAME key then trips the
# store's own MISMATCH check -> 422 -> only THEN does the key settle -> the
# 3rd submit is the one that finally books. Every "escolha outro horário"
# round currently costs two throwaway submits. A `code` the client can read
# without parsing the pt-BR sentence lets it settle the key on the FIRST 409
# instead, matching the L4 frontend follow-up this card hands off to.
#
# `message` stays the pt-BR sentence the SDR sees; `code` is the stable slug.
# Confirmed safe for the existing string-only consumer: ApiClient.
# extractErrorDetail() (frontend/app/_data/ApiClient.tsx) already JSON.
# stringifies any object `detail` instead of crashing — it just won't show a
# clean sentence until L4 reads `code` explicitly, which is out of scope here.
_DETAIL_CODE_SLOT_TAKEN = "slot_taken"
_DETAIL_CODE_NO_ADVISOR_FREE = "no_advisor_free"


def _slot_conflict_detail(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


# Categoria → display label (for SF FaixadePLInformada__c). Mirrors the
# frontend labels used today so the SF data stays comparable.
#
# FBI-3482: a redacão continua explicita porque este texto é GRAVADO no
# Salesforce e a forma é da casa — derivar de min/max produziria "R$ 50.000 a
# R$ 100.000", que não é o que está no histórico do campo. O que impede o
# dicionário de ficar atrás da matriz é o teste de paridade de chaves
# (test_fbi3482_pl_bands.py), não a boa vontade de quem edita.
_PATRIMONY_RANGE_LABELS: dict[str, str] = {
    "50k-100k": "R$ 50 Mil a R$ 100 Mil",
    "100k-300k": "R$ 100 Mil a R$ 300 Mil",
    "300k-5M": "R$ 300 Mil a R$ 5 Milhões",
    "5M+": "Acima de R$ 5 Milhões",
}


# ── shared setup ─────────────────────────────────────────────────────────


async def _resolve_sf_connections(user_email: str) -> tuple[Any, Any]:
    """Resolve (admin_sf, per_user_sf). 503 if JWT misconfigured, 403 if user lacks SF auth."""
    if not is_jwt_flow_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Salesforce JWT não configurado. Contate o administrador.",
        )
    loop = asyncio.get_event_loop()
    try:
        sf_user = await loop.run_in_executor(
            None, lambda: get_salesforce_connection_as_user(user_email)
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("JWT per-user auth failed for %s: %s", user_email, exc)
        sf_user = None
    if not sf_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Usuário {user_email} não possui conta Salesforce ou não está "
                f"autorizado no Connected App."
            ),
        )
    sf = get_salesforce_connection()
    if not sf:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível conectar ao Salesforce (admin connection).",
        )
    return sf, sf_user


async def _resolve_sdr_identity(sf: Any, user_email: str, override_name: Optional[str]) -> tuple[str, str]:
    """Look up the SDR's SF User Id + display name."""
    loop = asyncio.get_event_loop()
    rec = await loop.run_in_executor(
        None, lambda: resolve_sf_user_by_email(sf, user_email, ("Id", "Name"))
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Usuário Salesforce não encontrado para {user_email}",
        )
    return rec["Id"], rec.get("Name") or override_name or user_email


async def _fetch_lead(sf: Any, lead_id: str) -> dict[str, Any]:
    from app.api.v1.leads import LEAD_SOQL_FIELDS, _query_sf_leads, _validate_sf_id

    validated = _validate_sf_id(lead_id)
    soql = (
        f"SELECT {LEAD_SOQL_FIELDS}, IsConverted, ConvertedAccountId, "
        "ConvertedContactId, ConvertedOpportunityId FROM Lead "
        f"WHERE Id = '{validated}' AND IsDeleted = false"
    )
    loop = asyncio.get_event_loop()
    records = await loop.run_in_executor(None, lambda: _query_sf_leads(sf, soql))
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} não encontrado",
        )
    return records[0]


async def _fetch_account(sf: Any, account_id: str) -> dict[str, Any]:
    from app.api.v1.leads import _validate_sf_id

    validated = _validate_sf_id(account_id)
    loop = asyncio.get_event_loop()
    fields = (
        "Id, Name, OwnerId, Owner.Name, AccountSource, CreatedDate, "
        "(SELECT Id, Email, Phone FROM Contacts ORDER BY CreatedDate LIMIT 1)"
    )
    record = await loop.run_in_executor(
        None,
        lambda: sf.query(  # type: ignore
            f"SELECT {fields} FROM Account WHERE Id = '{validated}' AND IsDeleted = false"
        ),
    )
    if record.get("totalSize", 0) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} não encontrado",
        )
    acct = record["records"][0]
    acct["_consorcio_origin"] = await _account_consorcio_origin(sf, validated)
    return acct


async def _account_consorcio_origin(sf: Any, account_id: str) -> bool:
    """Async wrapper over the shared `account_has_consorcio_origin` contract —
    the single source of truth for consórcio origin, reused by every
    Account→Opportunity path (FBI-2386)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, lambda: account_has_consorcio_origin(sf, account_id)
    )


async def _resolve_converted_lead_advisor(
    sf: Any, record: dict[str, Any], request: QualifyRequest, sdr_sf_id: str,
) -> ConsorcioAdvisor:
    """Preserve the advisor already materialized by a partial Super R1.

    An existing exact-slot R1 is strongest evidence; otherwise use the
    Opportunity specialist/owner. Recovery must never run availability-based
    selection again: the original advisor appears busy precisely because the
    first attempt may already have created their Event.
    """
    from app.api.v1.leads import _validate_sf_id

    opportunity_id = record.get("ConvertedOpportunityId")
    if not opportunity_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead convertido sem Opportunity vinculada; acione o suporte.",
        )
    opportunity_id = _validate_sf_id(opportunity_id)
    event_dt = _event_datetime_brt(request.scheduled_date, request.scheduled_time)
    event_start_utc = event_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    loop = asyncio.get_event_loop()

    def lookup() -> Optional[dict[str, Any]]:
        events = sf.query(
            "SELECT OwnerId, Owner.Name, Owner.Email FROM Event "
            f"WHERE WhatId = '{opportunity_id}' AND Type = 'R1' "
            f"AND StartDateTime = {event_start_utc} ORDER BY CreatedDate DESC LIMIT 1"
        )
        if events.get("totalSize", 0) > 0:
            row = events["records"][0]
            owner = dict(row.get("Owner") or {})
            owner["Id"] = row.get("OwnerId")
            return owner
        opp = sf.query(
            "SELECT OwnerId, Owner.Name, Owner.Email, Owner.Alias, "
            "DWEspecialistaResponsavel__c, DWEspecialistaResponsavel__r.Name, "
            "DWEspecialistaResponsavel__r.Email FROM Opportunity "
            f"WHERE Id = '{opportunity_id}' LIMIT 1"
        )
        if opp.get("totalSize", 0) == 0:
            return None
        row = opp["records"][0]
        specialist = dict(row.get("DWEspecialistaResponsavel__r") or {})
        specialist["Id"] = row.get("DWEspecialistaResponsavel__c")
        if specialist["Id"]:
            return specialist
        owner = dict(row.get("Owner") or {})
        owner["Id"] = row.get("OwnerId")
        if owner["Id"] != sdr_sf_id and owner.get("Alias") != "FCAdmin":
            return owner
        return None

    user = await loop.run_in_executor(None, lookup)
    if not user or not user.get("Id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Lead convertido sem especialista recuperável. Abra a falha do "
                "Super R1 para concluir o roteamento manualmente."
            ),
        )
    active = await loop.run_in_executor(
        None, lambda: filter_active_user_ids(sf, [user["Id"]])
    )
    if user["Id"] not in active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O especialista original da recuperação está inativo no Salesforce.",
        )
    return ConsorcioAdvisor(
        sf_id=user["Id"],
        name=user.get("Name") or user["Id"],
        email=user.get("Email") or f"{user['Id']}@salesforce.invalid",
    )


async def _close_recovered_routing_failure(
    session: AsyncSession, recovery_key: str, user_email: str,
) -> bool:
    """Close the routing failure the first attempt left open. Idempotent.

    The UPDATE is scoped to `resolved_at IS NULL`, so running it again after a
    success is a no-op — which is what lets both the live path and the replay
    path call it without coordinating.
    """
    try:
        await RoutingFailureRepository(session).resolve_open_for_opportunity(
            opportunity_id=recovery_key,
            actor_email=user_email,
            note="Resolvida automaticamente por retry idempotente do Super R1.",
        )
        await session.commit()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Recovered Opportunity %s but failed to close old routing failure: %s",
            recovery_key, exc,
        )
        await session.rollback()
        return False


async def _run_converted_lead_recovery(
    *, request: QualifyRequest, sf: Any, sf_user: Any,
    user_email: str, sdr_sf_id: str, sdr_sf_name: str,
    session: AsyncSession, record: dict[str, Any],
    is_consorcio: bool, categoria: Optional[str], flow_label: FlowTaken,
) -> QualifyResponse:
    """Resume a Lead whose conversion committed but whose R1 did not finish.

    Shared by every synchronous flow that can receive an already converted Lead,
    because both halves of the recovery are indifferent to consórcio: the claim
    is scoped to the Opportunity (not the client's Idempotency-Key, so two
    retries with different keys still serialize), and the advisor is read back
    from Salesforce instead of re-picked by availability — the original advisor
    looks busy precisely because the first attempt already booked their Event,
    and re-picking would hand the meeting to someone else and add a second R1
    (create_r1_event dedupes on OwnerId, so a different owner is a new Event).
    """
    recovery_key = str(record.get("ConvertedOpportunityId") or request.record_id)
    recovery_hash = _qualify_request_fingerprint(request, user_email)
    claim = await idempotency_store.claim_or_replay(
        _RECOVERY_IDEMPOTENCY_SCOPE,
        _RECOVERY_IDEMPOTENCY_ACTOR,
        recovery_key,
        recovery_hash,
    )
    if claim.outcome == idempotency_store.BUSY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A recuperação desta Opportunity já está em andamento.",
        )
    if claim.outcome == idempotency_store.MISMATCH:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A Opportunity já possui uma recuperação para outro horário "
                "ou payload. Use a Account para um novo agendamento."
            ),
        )
    if claim.outcome == idempotency_store.HIT:
        replayed = QualifyResponse.model_validate(claim.replay)
        # The reconciliation below is best-effort, so a successful recovery can
        # end with the old routing failure still open and the response already
        # cached. Replaying re-attempts it: without this, the only path that
        # could ever close that row is the one the cache now short-circuits.
        if replayed.success:
            await _close_recovered_routing_failure(session, recovery_key, user_email)
        return replayed

    recovery_token = claim.owner_token
    recovery_hb_task = asyncio.create_task(
        _idempotency_heartbeat(
            _RECOVERY_IDEMPOTENCY_ACTOR,
            recovery_key,
            recovery_token,
            scope=_RECOVERY_IDEMPOTENCY_SCOPE,
        )
    )
    try:
        try:
            advisor = await _resolve_converted_lead_advisor(
                sf, record, request, sdr_sf_id
            )
        except HTTPException as exc:
            persisted = await RoutingFailureRepository(
                session
            ).advisor_for_open_opportunity(recovery_key)
            if not persisted:
                raise exc
            from app.api.v1.leads import _validate_sf_id

            advisor_id = _validate_sf_id(persisted["advisor_sf_user_id"])
            loop = asyncio.get_event_loop()
            active = await loop.run_in_executor(
                None, lambda: filter_active_user_ids(sf, [advisor_id])
            )
            if advisor_id not in active:
                raise exc
            user = await loop.run_in_executor(
                None,
                lambda: sf.query(
                    "SELECT Id, Name, Email FROM User "
                    f"WHERE Id = '{advisor_id}' LIMIT 1"
                ),
            )
            records = user.get("records", [])
            advisor = ConsorcioAdvisor(
                sf_id=advisor_id,
                name=(records[0].get("Name") if records else None)
                or persisted.get("advisor_name") or advisor_id,
                email=(records[0].get("Email") if records else None)
                or f"{advisor_id}@salesforce.invalid",
            )

        response = await _run_d0_lead_flow(
            request=request, sf_user=sf_user,
            user_email=user_email, sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name,
            lead_record=record,
            advisor_sf_id=advisor.sf_id, advisor_name=advisor.name,
            is_consorcio=is_consorcio, categoria=categoria,
            flow_label=flow_label, cluster=None,
            advisor_payload_overrides={"email": advisor.email},
        )
    except BaseException:
        # CancelledError is not an Exception subclass in Python 3.13, so a client
        # disconnect mid-flow has to be caught here too or the claim leaks and
        # the Opportunity stays unrecoverable.
        await _stop_heartbeat(recovery_hb_task)
        await idempotency_store.release(
            _RECOVERY_IDEMPOTENCY_SCOPE,
            _RECOVERY_IDEMPOTENCY_ACTOR,
            recovery_key,
            recovery_token,
        )
        raise

    await _stop_heartbeat(recovery_hb_task)
    if not response.success:
        await idempotency_store.release(
            _RECOVERY_IDEMPOTENCY_SCOPE,
            _RECOVERY_IDEMPOTENCY_ACTOR,
            recovery_key,
            recovery_token,
        )
        return response

    # Reconcile BEFORE caching the response. The other order lets a failed close
    # be sealed behind a HIT that returns without retrying it.
    await _close_recovered_routing_failure(session, recovery_key, user_email)

    # Salesforce is already committed at this point, so caching the reply is the
    # last, least important step: it must never turn a completed booking into a
    # 5xx. A raise here used to escape past the release handler above, leaving
    # the Opportunity claimed until the lease expired — a recovery that worked
    # answered 500 and then refused retries for the whole lease window. Releasing
    # instead costs a re-run, which the flow is idempotent for.
    try:
        await idempotency_store.finish(
            _RECOVERY_IDEMPOTENCY_SCOPE,
            _RECOVERY_IDEMPOTENCY_ACTOR,
            recovery_key,
            recovery_token,
            response.model_dump(mode="json"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Recovered Opportunity %s but failed to persist the replay: %s",
            recovery_key, exc,
        )
        try:
            await idempotency_store.release(
                _RECOVERY_IDEMPOTENCY_SCOPE,
                _RECOVERY_IDEMPOTENCY_ACTOR,
                recovery_key,
                recovery_token,
            )
        except Exception as release_exc:  # noqa: BLE001
            logger.warning(
                "Failed to release recovery claim for Opportunity %s: %s",
                recovery_key, release_exc,
            )
    return response


def _resolve_is_consorcio(
    *, is_account: bool, request: QualifyRequest, record: dict[str, Any]
) -> bool:
    """
    Consórcio routing decision.

    Lead: the SF Lead RecordType is the source of truth. Account: the SDR
    intent (request.service_type) OR the converting Lead's RecordType — the
    latter pins the FBI-2386 invariant so a converted consórcio lead can't
    silently fall back to investimentos via the Account route's defaulted
    service_type.
    """
    if is_account:
        if request.service_type == "consorcio":
            return True
        return record.get("_consorcio_origin") is True
    rt = record.get("RecordType")
    sf_rt = rt.get("DeveloperName") if isinstance(rt, dict) else None
    return sf_rt == "Consorcios"


def _patrimony_range_label(categoria: Optional[str], passed: Optional[str]) -> str:
    """Prefer categoria-derived FBI-2925 labels; fall back to client string."""
    if categoria and categoria in _PATRIMONY_RANGE_LABELS:
        return _PATRIMONY_RANGE_LABELS[categoria]
    if passed:
        return passed
    return ""


def _interest_to_string(interest: list[str]) -> str:
    return ";".join(i for i in interest if i and i.strip())


def _consorcio_interests_to_string(interest: Optional[list[str]]) -> Optional[str]:
    if interest is None:
        return None
    joined = ";".join(i for i in interest if i and i.strip())
    return joined or None


def _event_datetime_brt(d: Any, t: str) -> datetime:
    """Build a BRT-aware datetime from (date, 'HH:MM')."""
    hh, mm = (int(p) for p in t.split(":"))
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=_SP_TZ)


async def _eligible_advisor_ids_for_categoria(
    session: AsyncSession, categoria: str
) -> list[int]:
    """
    Eligible advisor pool for a categoria (FBI-2925).

    Filters makershub.dim_advisor by branch_office, position and level,
    excludes leadership, and drops unranked (no fct_advisor_ranking row
    for the latest business day) so calendar and qualify share the same pool.
    """
    spec = get_pool_spec(categoria)
    if not spec:
        return []
    ids = await RoutingRepository().get_advisor_ids_for_pool(
        session=session,
        branch_offices=list(spec.branch_offices),
        position=spec.position,
        advisor_level=spec.advisor_level,
    )
    if not ids:
        return []
    try:
        unranked = await AdvisorRepository().get_unranked_advisor_ids(
            session, spec.cluster
        )
        unranked_set = {int(x) for x in unranked}
        return [i for i in ids if i not in unranked_set]
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "unranked filter failed for %s (%s): %s — using full pool",
            categoria,
            spec.cluster,
            exc,
        )
        return ids


async def _narrow_pool_to_selected_slot(
    session: AsyncSession,
    pool_ids: list[int],
    request: QualifyRequest,
) -> list[int]:
    """Keep only pool advisors still free at the selected Graph slot.

    This is the read half of the availability guard. The write half — the
    transactional slot lock that closes the race between two concurrent
    SDRs — is acquired later, on the ONE advisor that actually gets picked
    (see :func:`_lock_selected_slot`). Locking the whole Graph-free pool
    here would block the slot for every advisor who was never booked.
    """
    if not request.scheduled_date or not request.scheduled_time:
        return pool_ids

    emails_by_id = await RoutingRepository().get_advisor_emails_by_ids(
        session, pool_ids
    )
    if not emails_by_id:
        return pool_ids

    # FBI-2987: verify_slot is now fail-CLOSED — a Graph error propagates as
    # HTTP 409 instead of returning the full input list. Graph success plus
    # an empty result is authoritative and must not fall back to the full
    # pool, or we would create a conflicting Salesforce event.
    free = await verify_slot(
        emails=list(emails_by_id.values()),
        scheduled_date=request.scheduled_date,
        scheduled_time=request.scheduled_time,
        duration_minutes=request.duration_minutes,
    )
    free_lc = {email.lower() for email in free}
    narrowed = [
        advisor_id
        for advisor_id, email in emails_by_id.items()
        if email.lower() in free_lc
    ]
    if not narrowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_slot_conflict_detail(
                _DETAIL_CODE_NO_ADVISOR_FREE,
                "Nenhum assessor livre no horário selecionado. "
                "Escolha outro horário.",
            ),
        )
    return narrowed


def _slot_lock_enabled() -> bool:
    """Kill-switch for item B1(b): default TRUE, unlike the R1_CHECK_ADVISOR_
    AGENDA / R1_TENTATIVE_BLOCKS flags in availability_service.py (those
    default false — new opt-in behavior). This one inverts the polarity
    on purpose: the lock is the FIX for double-booking, so it must stay ON
    unless someone explicitly turns it off. Reading it fresh on every call
    (no config.py caching) lets ops flip it in prod env vars without a
    redeploy if the ledger itself misbehaves — the same escape hatch B1(a)
    below needs when the table isn't there yet."""
    return os.environ.get("R1_SLOT_LOCK_ENABLED", "true").lower() != "false"


async def _lock_selected_slot(
    session: AsyncSession,
    *,
    advisor_email: Optional[str],
    scheduled_at: datetime,
    duration_minutes: int = MEETING_DURATION,
    employee_id: Optional[int] = None,
    categoria: Optional[str] = None,
    booking_ref: Optional[str] = None,
    source: str = "qualify",
    actor_email: str = "system@makershub",
) -> SlotLockAcquisition:
    """Reserve the picked advisor's calendar at ``scheduled_at`` (FBI-2987).

    ``verify_slot`` is a read: two concurrent SDRs both pass it, both pick
    the same advisor and both create a Salesforce Event — "duas agendas uma
    em cima da outra". This is the mutex that closes the window, keyed on the
    Outlook calendar identity (the e-mail). Returns False when a concurrent
    booking already holds the slot.

    An advisor with no e-mail on record cannot be Graph-verified either, so
    there is nothing to reserve: we log and let the booking through rather
    than turning a pre-existing degraded path into a hard 409.

    ``duration_minutes`` (item B1-c) must come from the caller's request —
    it feeds ``ends_at`` in the ledger row. Left at the MEETING_DURATION
    default it would misstate the interval for every 15/30/90/120-minute
    lead the pool also serves (grade: SLOT_INTERVAL=15min, caller range
    15..120), narrowing or widening the overlap window the exclusion
    constraint actually protects.

    Item B1(a) — deploy-ordering bridge: this backend has no migration
    runner (nothing under app/ reads db/migrations; Dockerfile.release goes
    straight to gunicorn), so ``makershub.advisor_slot_locks`` is created by
    hand and can lag behind a code deploy. Measured in prod:
    ``to_regclass('makershub.advisor_slot_locks')`` is NULL there today. If
    that gap hits this call site raw, ``UndefinedTable`` (42P01, wrapped by
    SQLAlchemy's asyncpg dialect as ``ProgrammingError`` — confirmed against
    PostgreSQL 16.14) propagates as HTTP 500 from OUTSIDE the try/except that
    wraps the Salesforce flow in ``_qualify_regular_d0``, and by that point
    ``confirm_routing`` has already committed the round-robin queue advance
    for the very advisor whose booking just 500'd — the rotation moves on to
    someone who was never scheduled. Degrading to ``True`` (book without a
    ledger row, the pre-FBI-2987 behavior) trades a temporarily-unenforced
    double-booking guard for not burning a queue slot on a deploy-ordering
    accident; B1(b)'s kill switch gives ops the same degrade on demand if the
    ledger itself is the problem instead.
    """
    if not _slot_lock_enabled():
        logger.warning(
            "slot lock disabled via R1_SLOT_LOCK_ENABLED=false: booking "
            "advisor_email=%s at %s proceeds with NO calendar reservation",
            advisor_email,
            scheduled_at.isoformat(),
        )
        return SlotLockAcquisition(acquired=True)
    if not advisor_email:
        logger.warning(
            "slot lock skipped: advisor_id=%s has no e-mail on record, so the "
            "calendar cannot be reserved for %s",
            employee_id,
            scheduled_at.isoformat(),
        )
        return SlotLockAcquisition(acquired=True)
    try:
        handle = await RoutingRepository().try_lock_slot(
            session=session,
            advisor_email=advisor_email,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            employee_id=employee_id,
            categoria=categoria,
            booking_ref=booking_ref,
            source=source,
            actor_email=actor_email,
        )
        valid_handle = handle if isinstance(handle, SlotLockHandle) else None
        return SlotLockAcquisition(acquired=handle is not None, handle=valid_handle)
    except ProgrammingError as exc:
        # UndefinedTable bridged here per B1(a) above. The failed INSERT
        # leaves the session's transaction aborted; roll back so the
        # booking flow that continues past this point (SF calls only, no
        # further DB use on this path today) doesn't inherit a poisoned
        # session before the Salesforce flow continues.
        if not session.is_active:
            await session.rollback()
        logger.error(
            "action=slot_lock_table_missing | advisor_email=%s | "
            "scheduled_at=%s | duration_minutes=%s | categoria=%s | "
            "booking_ref=%s | error=%s",
            advisor_email,
            scheduled_at.isoformat(),
            duration_minutes,
            categoria,
            booking_ref,
            exc,
        )
        return SlotLockAcquisition(acquired=True)


async def _settle_slot_lock(
    session: AsyncSession,
    *,
    handle: Optional[SlotLockHandle],
    response: QualifyResponse,
    actor_email: str,
    source: str,
) -> None:
    """Persist a positive terminal fact; unknown outcomes stay pending."""
    if handle is None:
        return
    event_id = (response.event_id or "").strip()
    outcome = response.event_write_outcome
    try:
        repo = RoutingRepository()
        if event_id:
            await repo.confirm_slot_lock(
                session, handle, event_id,
                source=source, actor_email=actor_email,
            )
        elif outcome in {"event_not_attempted", "event_not_created"}:
            await repo.mark_slot_lock_abandoned(
                session,
                handle,
                evidence_kind=outcome,
                evidence_detail="explicit Salesforce flow outcome",
                source=source,
                actor_email=actor_email,
            )
        else:
            logger.warning(
                "slot lock remains pending: lock_id=%s outcome=%s",
                handle.lock_id,
                outcome,
            )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "failed to settle slot lock %s: %s — lifecycle remains non-terminal",
            handle.lock_id,
            exc,
        )


async def _resolve_blocked_pool_fallback(
    session: AsyncSession,
    categoria: str,
    pool_ids: list[int],
    request: QualifyRequest,
) -> tuple[str, list[int], Optional[str]]:
    """
    Route 5M+ to the native Closer queue when all free consultants are blocked.

    The trigger is ranking-specific. Empty/unranked pools, calendar conflicts,
    absences and repository failures do not silently change the destination.
    Returning ``300k-5M`` is deliberate: the fallback consumes the Closer
    pool's existing round-robin queue, so a fallback lead counts toward the
    same workload sequence instead of creating a second queue that can pick the
    same Closer twice in a row.
    """
    spec = get_pool_spec(categoria)
    if not spec or spec.cluster != "Consultoria" or not pool_ids:
        return categoria, pool_ids, None

    try:
        blocked_ids = await AdvisorRepository().get_blocked_advisor_ids(session)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Consultoria ranking-block lookup failed; fallback disabled: %s",
            exc,
        )
        return categoria, pool_ids, None

    if not set(pool_ids).issubset(blocked_ids):
        return categoria, pool_ids, None

    fallback_ids = await _eligible_advisor_ids_for_categoria(
        session, CATEGORIA_300K_5M
    )
    if not fallback_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Todos os consultores estão bloqueados e não há Closer "
                "elegível para fallback."
            ),
        )
    fallback_ids = await _narrow_pool_to_selected_slot(
        session, fallback_ids, request
    )
    logger.warning(
        "action=super_r1_pool_fallback | surface=qualify | "
        "from_cluster=Consultoria | to_cluster=Closer | "
        "reason=all_consultants_ranking_blocked | consultant_ids=%s | "
        "closer_candidate_ids=%s",
        sorted(pool_ids),
        sorted(fallback_ids),
    )
    return CATEGORIA_300K_5M, fallback_ids, "Consultoria"


# ── flow handlers ────────────────────────────────────────────────────────



async def _run_d0_lead_flow(
    *,
    request: QualifyRequest, sf_user: Any,
    user_email: str, sdr_sf_id: str, sdr_sf_name: str,
    lead_record: dict[str, Any],
    advisor_sf_id: str, advisor_name: str,
    is_consorcio: bool,
    categoria: Optional[str],
    flow_label: FlowTaken,
    cluster: Optional[str],
    advisor_payload_overrides: Optional[dict[str, Any]] = None,
) -> QualifyResponse:
    """
    Common D+0 Lead path — invokes execute_r1_scheduling_flow with the
    advisor the caller already picked (or the fixed consórcio advisor).
    """
    from app.api.v1.leads import _sf_record_to_lead_info

    lead_data = _sf_record_to_lead_info(lead_record)
    if not request.scheduled_date or not request.scheduled_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="scheduled_date and scheduled_time are required for this flow",
        )
    event_dt = _event_datetime_brt(request.scheduled_date, request.scheduled_time)
    range_label = _patrimony_range_label(categoria, request.patrimony_range)
    interest_str = _interest_to_string(request.interesse_investimentos)
    consorcio_interest_str = _consorcio_interests_to_string(request.interesses_consorcios)

    validation_errors = validate_lead_update_data(
        patrimony_value=request.patrimony_value or 0,
        profissao=request.profissao,
        interesse=interest_str,
        description=request.description,
        is_consorcio=is_consorcio,
    )
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": "Dados inválidos", "errors": validation_errors},
        )

    loop = asyncio.get_event_loop()
    if lead_record.get("IsConverted"):
        converted_opp = lead_record.get("ConvertedOpportunityId")
        converted_account = lead_record.get("ConvertedAccountId")
        if not converted_opp or not converted_account:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lead convertido sem Account/Opportunity vinculada; acione o suporte.",
            )
        def flow():
            return execute_r1_resume_converted_lead_flow(
                lead_id=lead_data.id,
                opportunity_id=converted_opp,
                account_id=converted_account,
                contact_id=lead_record.get("ConvertedContactId"),
                lead_name=lead_data.name,
                patrimony_value=request.patrimony_value or 0,
                profissao=request.profissao,
                interesse_investimentos=interest_str,
                description=request.description,
                event_datetime=event_dt,
                advisor_salesforce_id=advisor_sf_id,
                advisor_name=advisor_name,
                sdr_salesforce_id=sdr_sf_id,
                sdr_name=sdr_sf_name,
                sdr_email=user_email,
                is_consorcio=is_consorcio,
                duration_minutes=request.duration_minutes,
                modalidade=request.modalidade,
            )
    else:
        def flow():
            return execute_r1_scheduling_flow(
                lead_id=lead_data.id,
                lead_name=lead_data.name,
                lead_email=lead_data.email,
                patrimony_value=request.patrimony_value or 0,
                patrimony_range=range_label,
                profissao=request.profissao,
                interesse_investimentos=interest_str,
                description=request.description,
                event_datetime=event_dt,
                advisor_salesforce_id=advisor_sf_id,
                advisor_name=advisor_name,
                sdr_salesforce_id=sdr_sf_id,
                sdr_name=sdr_sf_name,
                sdr_email=user_email,
                lead_source=lead_data.lead_source,
                is_consorcio=is_consorcio,
                duration_minutes=request.duration_minutes,
                modalidade=request.modalidade,
                sf_user_connection=sf_user,
                idade=request.idade,
                modalidade_calculo=request.modalidade_calculo,
                id_carta=request.id_carta,
                tomador_decisao=request.tomador_decisao,
                intuito_consorcio=request.intuito_consorcio,
                interesses_consorcios=consorcio_interest_str,
            )
    result = await loop.run_in_executor(None, flow)
    success = bool(result.get("success"))

    advisor_payload = QualifiedAdvisor(
        full_name=advisor_name,
        sf_user_id=advisor_sf_id,
        cluster=cluster,
        is_consorcio_fixed=is_consorcio,
    )
    if advisor_payload_overrides:
        for k, v in advisor_payload_overrides.items():
            setattr(advisor_payload, k, v)

    return QualifyResponse(
        success=success,
        flow_taken=flow_label,
        message=("R1 agendada" if success else "Falha no agendamento R1"),
        lead_id=lead_data.id,
        account_id=result.get("account_id"),
        contact_id=result.get("contact_id"),
        opportunity_id=result.get("opportunity_id"),
        event_id=result.get("event_id"),
        event_write_outcome=result.get("event_write_outcome", "write_started_unknown"),
        advisor=advisor_payload,
        scheduled_for=event_dt.isoformat(),
        categoria=categoria,
        steps_completed=list(result.get("steps_completed", [])),
        errors=list(result.get("errors", [])),
        sandbox_mode=bool(result.get("sandbox_mode")),
        raw_result=result,
    )


async def _run_d0_account_flow(
    *,
    request: QualifyRequest, sf_user: Any,
    user_email: str, sdr_sf_id: str, sdr_sf_name: str,
    account_record: dict[str, Any],
    advisor_sf_id: str, advisor_name: str,
    is_consorcio: bool,
    categoria: Optional[str],
    flow_label: FlowTaken,
    cluster: Optional[str],
) -> QualifyResponse:
    """Common D+0 Account path — invokes execute_r1_from_opportunity_flow."""
    if not request.scheduled_date or not request.scheduled_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="scheduled_date and scheduled_time are required for this flow",
        )
    event_dt = _event_datetime_brt(request.scheduled_date, request.scheduled_time)
    range_label = _patrimony_range_label(categoria, request.patrimony_range)
    interest_str = _interest_to_string(request.interesse_investimentos)
    consorcio_interest_str = _consorcio_interests_to_string(request.interesses_consorcios)

    # Restore parity with legacy /account/{id}/schedule-r1 (raise via
    # _schedule_r1_validation_detail): validate business data before any SF
    # write so the SDR gets a clean 422 instead of a downstream SF
    # validation-rule error. Mirrors the call site in _run_d0_lead_flow.
    validation_errors = validate_lead_update_data(
        patrimony_value=request.patrimony_value or 0,
        profissao=request.profissao,
        interesse=interest_str,
        description=request.description,
        is_consorcio=is_consorcio,
    )
    if validation_errors:
        from app.api.v1.leads import _schedule_r1_validation_detail

        # Same semantics as the legacy endpoint (FBI-2393/FBI-2435): the 422
        # explains itself only when the consórcio regime came from the
        # Account's converted-Lead origin, not from the caller's explicit
        # service_type.
        consorcio_from_origin = (
            is_consorcio
            and request.service_type != "consorcio"
            and account_record.get("_consorcio_origin") is True
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_schedule_r1_validation_detail(
                validation_errors, consorcio_from_origin=consorcio_from_origin
            ),
        )

    contacts = (account_record.get("Contacts") or {}).get("records", [])
    contact_id = contacts[0]["Id"] if contacts else None

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: execute_r1_from_opportunity_flow(
            source_opp_id=None,
            account_id=account_record["Id"],
            contact_id=contact_id,
            client_name=account_record.get("Name") or "Cliente",
            patrimony_value=request.patrimony_value or 0,
            patrimony_range=range_label,
            profissao=request.profissao,
            interesse_investimentos=interest_str,
            description=request.description,
            event_datetime=event_dt,
            advisor_salesforce_id=advisor_sf_id,
            advisor_name=advisor_name,
            sdr_salesforce_id=sdr_sf_id,
            sdr_name=sdr_sf_name,
            sdr_email=user_email,
            lead_source=account_record.get("AccountSource"),
            duration_minutes=request.duration_minutes,
            modalidade=request.modalidade,
            sf_user_connection=sf_user,
            is_consorcio=is_consorcio,
            idade=request.idade,
            modalidade_calculo=request.modalidade_calculo,
            id_carta=request.id_carta,
            tomador_decisao=request.tomador_decisao,
            intuito_consorcio=request.intuito_consorcio,
            interesses_consorcios=consorcio_interest_str,
        ),
    )
    success = bool(result.get("success"))
    return QualifyResponse(
        success=success,
        flow_taken=flow_label,
        message=("R1 agendada" if success else "Falha no agendamento R1"),
        account_id=account_record["Id"],
        contact_id=contact_id or result.get("contact_id"),
        opportunity_id=result.get("opportunity_id"),
        event_id=result.get("event_id"),
        event_write_outcome=result.get("event_write_outcome", "write_started_unknown"),
        advisor=QualifiedAdvisor(
            full_name=advisor_name,
            sf_user_id=advisor_sf_id,
            cluster=cluster,
            is_consorcio_fixed=is_consorcio,
        ),
        scheduled_for=event_dt.isoformat(),
        categoria=categoria,
        steps_completed=list(result.get("steps_completed", [])),
        errors=list(result.get("errors", [])),
        sandbox_mode=bool(result.get("sandbox_mode")),
        raw_result=result,
    )


async def _triage_owner_routing(
    session: AsyncSession, spec: PoolSpec, categoria: str
) -> ConfirmRoutingResponse:
    """
    FBI-3491: a faixa está em triagem (`PoolSpec.triage_level`) — vai inteira
    para a pessoa desse nível na área (hoje a Head da Consultoria), sem pool,
    sem fila e sem os filtros de ausência, suspensão e ranking que
    `select_best_advisor_for_queue` aplica. Ela não é o destino final da
    reunião: repassa cada uma à mão.

    Quem ocupa o nível vem do cadastro de assessores, igual ao pool do
    rodízio. Sem ninguém no nível, 409 com a causa escrita — não um desvio
    silencioso para o rodízio, que mandaria a faixa para quem o negócio tirou
    dela.
    """
    row = await RoutingRepository().get_triage_owner(
        session, list(spec.branch_offices), spec.triage_level or ""
    )
    if row is None:
        logger.error(
            "action=super_r1_triage_owner_missing | cluster=%s | level=%s | "
            "categoria=%s",
            spec.cluster, spec.triage_level, categoria,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Nenhuma pessoa ativa com nível {spec.triage_level} na área "
                f"{spec.branch_office} para receber a faixa {categoria}. "
                "Confira o cadastro de assessores."
            ),
        )
    return ConfirmRoutingResponse(
        selected_cluster=spec.cluster,
        categoria=categoria,
        selected_advisor=SelectedAdvisorInfo(
            employee_id=row["employee_id"],
            full_name=row["full_name"],
            team=row["team"],
            advisor_level=row["advisor_level"],
            email_address=row["email_address"],
            total_points=0,
            overall_ranking=None,
        ),
    )


async def _qualify_regular_d0(
    *, request: QualifyRequest, sf: Any, sf_user: Any,
    user_email: str, sdr_sf_id: str, sdr_sf_name: str,
    session: AsyncSession, is_account: bool, record: dict[str, Any],
    categoria: str,
) -> QualifyResponse:
    """Regular cluster D+0: cluster + advisor pick, then SF schedule."""
    if not is_account and record.get("IsConverted"):
        return await _run_converted_lead_recovery(
            request=request, sf=sf, sf_user=sf_user, user_email=user_email,
            sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name, session=session,
            record=record, is_consorcio=False, categoria=categoria,
            flow_label="regular_d0",
        )

    # FBI-3491: faixa em triagem (PoolSpec.triage_level) não passa por pool,
    # agenda, fallback nem fila. Sem triagem, o ramo de baixo é o de antes.
    spec = get_pool_spec(categoria)
    # Narrowed once so the type checker carries the proof into every use below.
    triage_spec = spec if spec is not None and spec.triage_level is not None else None
    if triage_spec is not None:
        routing_result = await _triage_owner_routing(session, triage_spec, categoria)
        fallback_from_cluster = None
        logger.info(
            "action=super_r1_triage_selected | cluster=%s | categoria=%s | "
            "employee_id=%s | agenda_checked=false",
            triage_spec.cluster, categoria, routing_result.selected_advisor.employee_id,
        )
    else:
        pool_ids = await _eligible_advisor_ids_for_categoria(session, categoria)
        if not pool_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Nenhum assessor elegível para a categoria {categoria}.",
            )

        pool_ids = await _narrow_pool_to_selected_slot(session, pool_ids, request)
        routing_categoria, pool_ids, fallback_from_cluster = (
            await _resolve_blocked_pool_fallback(
                session, categoria, pool_ids, request
            )
        )

        routing = RoutingService(RoutingRepository(), session)
        sandbox = GetSettings().sfIsSandbox
        # FBI-2946: the meeting date drives the absence filter. This is D+0, so it
        # is normally today — but passing it explicitly keeps the D+0 and D+1 paths
        # on the same contract and covers the edge where a same-day booking is made
        # right after the advisor's vacation starts.
        routing_result = await routing.confirm_routing(
            categoria=routing_categoria,
            available_advisor_ids=pool_ids,
            sandbox_mode=sandbox,
            target_date=request.scheduled_date,
        )
        if not routing_result or not routing_result.selected_advisor:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Falha ao selecionar assessor para a categoria {categoria}.",
            )
    sel = routing_result.selected_advisor
    # SelectedAdvisorInfo declara employee_id (FBI-2722); `sel.advisor_id` era
    # AttributeError vivo — o D+0 morria aqui mesmo com o routing saudavel.
    advisor_sf_id = await get_advisor_salesforce_id(
        session, sel.employee_id, advisor_name=sel.full_name
    )
    if not advisor_sf_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Salesforce ID não encontrado para {sel.full_name}",
        )
    await _require_active_advisor(
        sf=sf, advisor_sf_id=advisor_sf_id, advisor_name=sel.full_name,
    )

    if fallback_from_cluster:
        logger.warning(
            "action=super_r1_pool_fallback_selected | from_cluster=%s | "
            "to_cluster=%s | original_categoria=%s | routing_categoria=%s | "
            "advisor_id=%s",
            fallback_from_cluster,
            routing_result.selected_cluster,
            categoria,
            routing_categoria,
            sel.employee_id,
        )

    advisor_overrides = {
        "advisor_id": sel.employee_id,
        "email": sel.email_address,
        "team": sel.team,
        "advisor_level": sel.advisor_level,
        "cluster": routing_result.selected_cluster,
    }

    # FBI-2987 GAP 2: reserve the picked advisor's calendar before the SF write.
    #
    # Comment correction (item L1 audit): confirm_routing above committed only
    # the QUEUE position update. It does NOT commit a deficit update for any
    # of the 4 live categorias — all four have a PoolSpec (get_pool_spec),
    # so confirm_routing always delegates to confirm_pool_routing, whose body
    # calls update_advisor_queue_position_for_queue and NEVER calls
    # update_deficits. update_deficits only runs from confirm_routing's
    # non-pool legacy branch, which no live categoria reaches today. A prior
    # version of this comment claimed "queue/deficit updates" — that second
    # half was false and is corrected here.
    #
    # The lock is taken here — on the single advisor actually chosen. It is
    # settled only from an explicit Event outcome; exceptions/cancellation
    # stay pending because they do not prove whether Salesforce committed.
    # A request with no slot has nothing to reserve; the flows below reject it
    # with 422.
    scheduled_at = (
        _event_datetime_brt(request.scheduled_date, request.scheduled_time)
        if request.scheduled_date and request.scheduled_time
        else None
    )
    lock_acquisition = SlotLockAcquisition(acquired=True)
    if scheduled_at and triage_spec is not None:
        # FBI-3491: quem faz a triagem pode ter mais de uma reunião no mesmo
        # horário — repassa cada uma, então o horário dela não é o da reunião
        # real. Reservar em advisor_slot_locks recusaria a segunda 5M+ do mesmo
        # horário com 409 slot_taken, que é exatamente o que o card manda
        # evitar. Mesmo padrão dos outros dois "reserva dispensada" de
        # _lock_selected_slot: segue sem linha no ledger, com log.
        logger.warning(
            "action=super_r1_triage_lock_skipped | cluster=%s | "
            "employee_id=%s | scheduled_at=%s | booking_ref=%s",
            triage_spec.cluster,
            sel.employee_id,
            scheduled_at.isoformat(),
            request.record_id,
        )
    elif scheduled_at:
        lock_acquisition = await _lock_selected_slot(
            session,
            advisor_email=sel.email_address,
            scheduled_at=scheduled_at,
            duration_minutes=request.duration_minutes,
            employee_id=sel.employee_id,
            categoria=categoria,
            booking_ref=request.record_id,
            source="qualify_regular_d0",
            actor_email=user_email,
        )
        if not isinstance(lock_acquisition, SlotLockAcquisition):
            lock_acquisition = SlotLockAcquisition(acquired=bool(lock_acquisition))
    if not lock_acquisition:
        # No retry with the next pool advisor on purpose: re-running
        # confirm_routing would increment the round-robin queue a second time
        # for the advisor that just lost the race, skewing the rotation for
        # every later lead. Losing this race means two SDRs booked the same
        # advisor and slot within the same instant, so a 409 asking for
        # another slot is the honest answer. Consórcio can fall through to the
        # next candidate because its pick has no queue side effect.
        #
        # TODO(FBI-2987 item L1, reported not implemented): the queue
        # position for (sel.employee_id, categoria, routing_result.
        # selected_cluster) stays advanced by +1 here even though this
        # advisor never got the meeting — confirm_pool_routing's
        # update_advisor_queue_position_for_queue call above already
        # committed before this lock was even attempted, and there is no
        # transaction spanning both to roll back. Measured rate ~0.1% (1 in
        # ~1000 bookings). The correct fix is a decrement counterpart in
        # RoutingRepository — e.g. `decrement_advisor_queue_position_for_
        # queue(session, advisor_id, categoria, cluster)`, symmetric to
        # `update_advisor_queue_position_for_queue` (same UPSERT key,
        # `queue_position - 1` floored at 0) — called right here, before the
        # raise. That method does not exist today and routing_repo.py is out
        # of scope for this task (edited by another agent in this PR), so it
        # is intentionally NOT added in this file. Whoever owns
        # routing_repo.py next needs to add it and this call site needs to
        # invoke it.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_slot_conflict_detail(
                _DETAIL_CODE_SLOT_TAKEN,
                "O horário selecionado acabou de ser reservado para este "
                "assessor. Escolha outro horário.",
            ),
        )

    try:
        if is_account:
            # account path
            response = await _run_d0_account_flow(
                request=request, sf_user=sf_user,
                user_email=user_email, sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name,
                account_record=record,
                advisor_sf_id=advisor_sf_id, advisor_name=sel.full_name,
                is_consorcio=False, categoria=categoria,
                flow_label="regular_d0", cluster=routing_result.selected_cluster,
            )
            if response.advisor:
                for k, v in advisor_overrides.items():
                    setattr(response.advisor, k, v)
        else:
            response = await _run_d0_lead_flow(
                request=request, sf_user=sf_user,
                user_email=user_email, sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name,
                lead_record=record,
                advisor_sf_id=advisor_sf_id, advisor_name=sel.full_name,
                is_consorcio=False, categoria=categoria,
                flow_label="regular_d0", cluster=routing_result.selected_cluster,
                advisor_payload_overrides=advisor_overrides,
            )
    except BaseException:
        # Cancellation/exception has an unknown Salesforce write point. It is
        # not evidence of abandonment, so reconciliation keeps it pending.
        raise

    if scheduled_at:
        await _settle_slot_lock(
            session,
            handle=lock_acquisition.handle,
            response=response,
            actor_email=user_email,
            source="qualify_regular_d0",
        )
    return response



async def _select_consorcio_advisor_with_lock(
    pool: list[ConsorcioAdvisor],
    request: QualifyRequest,
    session: Optional[AsyncSession] = None,
    *,
    actor_email: str = "system@makershub",
) -> tuple[ConsorcioAdvisor, SlotLockAcquisition]:
    """
    Pick one advisor from the consórcio tier pool (FBI-2387).

    Availability-first in stable order: the first pool advisor still free at
    the chosen slot ("um depois o outro" — fall to the next when the first
    is busy), via verify_slot, and whose calendar we can actually reserve.

    FBI-2987: hard 409 when nobody is free. Two prior behaviors were removed:
      - `len(pool) == 1` short-circuit with NO Graph call (a single-advisor
        tier whose only member was busy still got booked, double-booking).
      - `return pool[0]` fail-open when verify_slot returned `[]` (also
        double-booked the busy advisor).

    The slot lock applies here too: consórcio shares the advisors' Outlook
    calendars with every other flow, so a Graph-free advisor who loses the
    lock race is skipped and the next candidate is tried. Losing the race is
    not an error for this pool — "um depois o outro" already means falling
    through to the next advisor.

    ``session=None`` skips the lock (no-DB contexts): the Graph check still
    decides the pick.
    """
    if request.scheduled_date and request.scheduled_time:
        # verify_slot now raises HTTP 409 on Graph errors (fail-closed) —
        # no special handling needed here for the auth/request path.
        free = await verify_slot(
            emails=[a.email for a in pool],
            scheduled_date=request.scheduled_date,
            scheduled_time=request.scheduled_time,
            duration_minutes=request.duration_minutes,
        )
        free_lc = {e.lower() for e in free}
        scheduled_at = _event_datetime_brt(
            request.scheduled_date, request.scheduled_time
        )
        for advisor in pool:
            if advisor.email.lower() not in free_lc:
                continue
            if session is None:
                return advisor, SlotLockAcquisition(acquired=True)
            acquisition = await _lock_selected_slot(
                session,
                advisor_email=advisor.email,
                scheduled_at=scheduled_at,
                duration_minutes=request.duration_minutes,
                booking_ref=request.record_id,
                source="qualify_consorcio_d0",
                actor_email=actor_email,
            )
            if acquisition:
                if not isinstance(acquisition, SlotLockAcquisition):
                    acquisition = SlotLockAcquisition(acquired=True)
                return advisor, acquisition
            logger.info(
                "consorcio slot lock lost for %s at %s — trying the next "
                "advisor in the tier pool",
                advisor.email,
                scheduled_at.isoformat(),
            )
        # Nobody free (or every free advisor lost the race) — raise instead of
        # falling open to pool[0].
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_slot_conflict_detail(
                _DETAIL_CODE_NO_ADVISOR_FREE,
                "Nenhum assessor do tier de consórcio livre no horário "
                "selecionado. Escolha outro horário.",
            ),
        )
    # No slot context (shouldn't happen for consórcio — the request schema
    # requires scheduled_date/scheduled_time for the consórcio flow), so keep
    # the historical first-pick behavior rather than raising.
    return pool[0], SlotLockAcquisition(acquired=True)


async def _select_consorcio_advisor(
    pool: list[ConsorcioAdvisor],
    request: QualifyRequest,
    session: Optional[AsyncSession] = None,
) -> ConsorcioAdvisor:
    """Compatibility facade for callers that only need the selected advisor."""
    advisor, _ = await _select_consorcio_advisor_with_lock(pool, request, session)
    return advisor


async def _record_routing_failure(
    *, session: AsyncSession, request: QualifyRequest, response: QualifyResponse,
    user_email: str,
) -> None:
    """
    Registra um roteamento que terminou em falha, para a tela de Config Super R1.

    Best-effort e em transação própria: falhar ao registrar a falha não pode
    derrubar a resposta ao SDR nem mascarar o resultado do Salesforce. Só grava a
    fonte D+0 — o D+1 já tem a própria linha em pending_d1_routings, e duplicar
    faria a mesma submissão aparecer duas vezes na lista.
    """
    if (response.flow_taken or "").endswith("_d1"):
        return

    try:
        advisor = response.advisor
        await RoutingFailureRepository(session).record(
            submitted_by_email=user_email or None,
            flow_taken=str(response.flow_taken) if response.flow_taken else None,
            is_consorcio=bool(advisor.is_consorcio_fixed) if advisor else False,
            categoria=response.categoria,
            cluster=advisor.cluster if advisor else None,
            advisor_sf_user_id=advisor.sf_user_id if advisor else None,
            advisor_name=advisor.full_name if advisor else None,
            record_id=request.record_id,
            lead_id=response.lead_id,
            account_id=response.account_id,
            contact_id=response.contact_id,
            opportunity_id=response.opportunity_id,
            event_id=response.event_id,
            # FBI-4272: pass the `date` object through, never `.isoformat()`.
            # The repository binds this param with CAST(:scheduled_date AS date),
            # which makes asyncpg encode it as a binary date and call
            # `.toordinal()` on the value. A str has no such method, so the whole
            # INSERT died with DataError and the audit row was never written —
            # silently, because the caller swallows the exception. Measured on
            # 2026-09-17: 4 failures logged and the table had 0 rows since the
            # FBI-2903 feature shipped on 2026-08-04.
            scheduled_date=request.scheduled_date,
            scheduled_time=request.scheduled_time,
            steps_completed=list(response.steps_completed or []),
            errors=[str(e) for e in (response.errors or [])],
            message=response.message,
        )
        await session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to record Super R1 routing failure: %s", exc)
        try:
            await session.rollback()
        except Exception:  # noqa: BLE001
            pass


async def _require_active_advisor(
    *, sf: Any, advisor_sf_id: str, advisor_name: str
) -> None:
    """
    409 quando o assessor sorteado está inativo no Salesforce.

    O caminho regular resolve o assessor por `dim_advisor.is_active` no warehouse,
    que não é a mesma coisa que `User.IsActive` no Salesforce — as duas fontes
    divergem e nada reconcilia. Quando divergem, o Salesforce recusa as gravações
    de OwnerId depois que o Lead já converteu, e a Opportunity fica sem dono.

    Recusa em vez de sortear outro: pular um assessor mexeria na fila do
    RoutingService, o que é decisão de roteamento e não de validação.
    """
    loop = asyncio.get_event_loop()
    active = await loop.run_in_executor(
        None, lambda: filter_active_user_ids(sf, [advisor_sf_id]),
    )
    if advisor_sf_id in active:
        return

    logger.error(
        "assessor inativo no Salesforce sorteado pelo roteamento regular: "
        "%s (%s)", advisor_name, advisor_sf_id,
    )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"O assessor {advisor_name} ({advisor_sf_id}) está inativo no Salesforce. "
            "A marcação foi bloqueada para não gerar oportunidade sem dono — "
            "atualize o cadastro do assessor."
        ),
    )


async def drop_inactive_consorcio_advisors(
    *, sf: Any, pool: list[ConsorcioAdvisor],
    resolution: ConsorcioPoolResolution, sdr_email: str,
) -> list[ConsorcioAdvisor]:
    """
    The pool minus the advisors whose Salesforce User is inactive.

    The consórcio routing target comes from env (fixed advisor, per-SDR override
    or tier pool), so a deactivation in Salesforce cannot invalidate it — the
    booking still resolves to that id and Salesforce then refuses to make it the
    owner of the Account, the Contact and the R1 Event. Without the R1 Event the
    stage advance is blocked too, leaving the Opportunity converted but ownerless
    on the admin queue, which no retry can undo.

    Checking here means the booking is rejected before the Lead converts, while
    failing is still clean. A partially deactivated pool keeps working on the
    advisors that are left.
    """
    loop = asyncio.get_event_loop()
    active_ids = await loop.run_in_executor(
        None, lambda: filter_active_user_ids(sf, [a.sf_id for a in pool]),
    )
    active = [a for a in pool if a.sf_id in active_ids]

    if len(active) == len(pool):
        return pool

    dropped = [a for a in pool if a.sf_id not in active_ids]
    if active:
        logger.error(
            "consorcio advisor inativo no Salesforce, removido do pool: "
            "tier=%s source=%s inativos=%s restantes=%s sdr=%s",
            resolution.tier, resolution.source,
            [(a.email, a.sf_id) for a in dropped],
            [a.email for a in active], sdr_email,
        )
        return active

    logger.error(
        "consorcio sem assessor ativo: tier=%s source=%s inativos=%s sdr=%s",
        resolution.tier, resolution.source,
        [(a.email, a.sf_id) for a in dropped], sdr_email,
    )
    # Detalhe em texto corrido, não dict: o ApiClient do frontend joga um detail
    # objeto em JSON.stringify e o SDR leria JSON cru na tela.
    quem = ", ".join(f"{a.name} ({a.sf_id})" for a in dropped)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"O assessor de consórcio configurado está inativo no Salesforce: {quem}. "
            "A marcação foi bloqueada para não gerar oportunidade sem dono — "
            "atualize o assessor em Gerenciamento → Config Super R1."
        ),
    )


async def _qualify_consorcio(
    *, request: QualifyRequest, sf: Any, sf_user: Any,
    user_email: str, sdr_sf_id: str, sdr_sf_name: str,
    session: AsyncSession, is_account: bool, record: dict[str, Any],
) -> QualifyResponse:
    """
    Consórcio — PL-tier advisor pool, no cluster routing (FBI-2387).

    PL >= 1MM and 300k+ route to their tier pool; PL < 300k keeps the fixed
    advisor. The advisor is picked availability-first from the tier pool (the one
    free at the chosen slot, stable order = "um depois o outro").
    Always synchronous regardless of scheduled date — the Event lands on the
    advisor's calendar at the chosen slot, today or in the future.
    flow_taken stays `consorcio_d0` either way (no batch involved).

    Who each tier routes to is configuration, read from the database (admin page
    Gerenciamento → Config Super R1) with the env as fallback — FBI-2903.
    """
    if not is_account and record.get("IsConverted"):
        return await _run_converted_lead_recovery(
            request=request, sf=sf, sf_user=sf_user, user_email=user_email,
            sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name, session=session,
            record=record, is_consorcio=True, categoria=None,
            flow_label="consorcio_d0",
        )

    config = await load_consorcio_config(session)
    resolution = resolve_consorcio_pool(
        request.patrimony_value, sdr_email=user_email, config=config,
    )
    pool = await drop_inactive_consorcio_advisors(
        sf=sf, pool=resolution.advisors, resolution=resolution, sdr_email=user_email,
    )
    advisor, lock_acquisition = await _select_consorcio_advisor_with_lock(
        pool, request, session, actor_email=user_email
    )
    if resolution.source == "tier_pool":
        # Activation observability (FBI-2397/FBI-2436): logged whenever the
        # tier pool is actually in use — including a 1-entry pool, which the
        # old `len(pool) > 1` proxy silently skipped.
        logger.info(
            "consorcio tier pool booking: tier=%s pl=%s pool=%s selected=%s sdr=%s",
            resolution.tier,
            request.patrimony_value,
            [a.email for a in pool],
            advisor.email,
            user_email,
        )
    elif resolution.tier is not None and resolution.source == "fixed":
        # FBI-2526: a tier-eligible lead (300k+/1MM+) fell back to the fixed
        # advisor because CONSORCIO_POOLS is unconfigured/invalid for this tier.
        # The happy-path log above never fires for this case, so it was silent —
        # which is how the feature shipped dormant. Surface it loudly so a
        # missing prod config is caught in minutes, not weeks.
        logger.warning(
            "consorcio tier-eligible lead routed to FIXED advisor (pool "
            "unconfigured for tier): tier=%s pl=%s selected=%s sdr=%s — set "
            "CONSORCIO_POOLS for this tier",
            resolution.tier,
            request.patrimony_value,
            advisor.email,
            user_email,
        )
    else:
        # Abaixo da faixa mínima não existe pool e o roteamento é o assessor fixo
        # por desenho, então nenhum dos dois logs acima dispara. Esse silêncio é o
        # que deixou o assessor fixo apontando pra usuário desativado por semanas:
        # é o caminho de MAIOR volume e não deixava rastro nenhum.
        logger.info(
            "consorcio fixed advisor booking (abaixo da faixa de pool): "
            "pl=%s selected=%s sdr=%s",
            request.patrimony_value,
            advisor.email,
            user_email,
        )
    scheduled_at = (
        _event_datetime_brt(request.scheduled_date, request.scheduled_time)
        if session is not None
        and request.scheduled_date
        and request.scheduled_time
        else None
    )
    try:
        if is_account:
            response = await _run_d0_account_flow(
                request=request, sf_user=sf_user,
                user_email=user_email, sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name,
                account_record=record,
                advisor_sf_id=advisor.sf_id, advisor_name=advisor.name,
                is_consorcio=True, categoria=None,
                flow_label="consorcio_d0", cluster=None,
            )
        else:
            response = await _run_d0_lead_flow(
                request=request, sf_user=sf_user,
                user_email=user_email, sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name,
                lead_record=record,
                advisor_sf_id=advisor.sf_id, advisor_name=advisor.name,
                is_consorcio=True, categoria=None,
                flow_label="consorcio_d0", cluster=None,
                advisor_payload_overrides={"email": advisor.email},
            )
    except BaseException:
        raise

    if scheduled_at:
        await _settle_slot_lock(
            session,
            handle=lock_acquisition.handle,
            response=response,
            actor_email=user_email,
            source="qualify_consorcio_d0",
        )
    return response


async def _qualify_regular_d1(
    *, request: QualifyRequest, sf: Any, sf_user: Any,
    user_email: str, sdr_sf_id: str, sdr_sf_name: str,
    session: AsyncSession, is_account: bool, record: dict[str, Any],
    categoria: str,
) -> QualifyResponse:
    """
    Regular D+1 deferred routing. Lock cluster now (deficit update),
    write a `pending_d1_routings` row, partially convert Lead/Account so
    the Opp exists at submission. The 21:00 BRT batch picks the advisor.
    """
    if not request.scheduled_date or not request.scheduled_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="scheduled_date and scheduled_time are required for D+1",
        )

    # D+1 has no resume path. STEP 2 of execute_r1_partial_flow_lead converts
    # unconditionally and returns BEFORE filling opportunity_id, so a converted
    # Lead here fails in a shape _is_resumable_converted_lead_failure cannot see
    # (opportunity_id is None) and qualify() caches the failure — the same
    # 409-forever chain this flow's D+0 sibling resumes out of. Rejecting before
    # the pending row and the SF write keeps the Account route as the only way
    # to open a new Opp for an already converted Lead.
    if not is_account and record.get("IsConverted"):
        converted_acct = record.get("ConvertedAccountId")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Lead {request.record_id} já foi convertido"
                + (
                    f". Use a Account {converted_acct} para criar nova Opp."
                    if converted_acct else "."
                )
            ),
        )

    settings = GetSettings()
    repo = RoutingRepository()
    routing = RoutingService(repo, session)

    spec = get_pool_spec(categoria)
    best_cluster = spec.cluster if spec else await routing._calculate_best_cluster(categoria)  # noqa: SLF001
    if not best_cluster:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Falha ao calcular cluster/pool para {categoria}.",
        )

    # FBI-2987 GAP 1: D+1 also verifies availability at SUBMIT time. The
    # external Airflow batch (21:00 BRT) cannot be trusted to re-check
    # Graph, and even if it did, the SDR needs to know NOW if the chosen
    # slot is busy — otherwise a busy advisor is handed the meeting later
    # at the batch window and the slot has to be re-negotiated with the
    # client. _narrow_pool_to_selected_slot raises HTTP 409 when nobody in
    # the pool is free, which reaches the SDR as "escolha outro horário" —
    # same UX as D+0.
    #
    # No slot lock here on purpose: the advisor is picked by the batch, not
    # now, so there is nothing to reserve. Locking the whole eligible pool
    # at submit time would block the slot for every advisor who never got
    # the meeting. The D+1 lock belongs to the batch that does the pick.
    pool_ids = await _eligible_advisor_ids_for_categoria(session, categoria)
    if pool_ids:
        await _narrow_pool_to_selected_slot(session, pool_ids, request)

    interest_str = _interest_to_string(request.interesse_investimentos)
    range_label = _patrimony_range_label(categoria, request.patrimony_range)
    placeholder = settings.sfEffectivePlaceholderOwnerId

    # Resolve lead/account ids needed for the pending row up-front so we can
    # persist the booking BEFORE touching Salesforce.
    initial_lead_id: str = ""
    initial_account_id: Optional[str] = None
    ld = None
    if is_account:
        initial_account_id = record["Id"]
    else:
        from app.api.v1.leads import _sf_record_to_lead_info
        ld = _sf_record_to_lead_info(record)
        initial_lead_id = ld.id

    # ─── PHASE 1 ─────────────────────────────────────────────────────────
    # Reserve the pending_d1_routings row up-front with NULL SF IDs and
    # commit immediately. This guarantees that the SDR's submission survives
    # a process crash anywhere in the SF write below. If the container dies
    # after the partial SF flow but before the SF-IDs UPDATE (i.e. the
    # Aline-2026-05-27 incident), this row stays as recoverable evidence.
    # Recovery is owned by the d1 batch's `reconcile_orphan_rows` step
    # (airflow-dags), which runs before load_pending_rows: for a Lead it reads
    # ConvertedOpportunityId; for an Account (no Lead) it resolves the Opp
    # best-effort by AccountId (newest — an Account can have N Opps). The batch
    # excludes opportunity_id IS NULL rows, so a survivor is never stamped
    # processed_at until reconciliation fills its Opp.
    pending_id = await repo.insert_pending_d1_routing(
        session=session,
        lead_id=initial_lead_id,
        lead_type="account" if is_account else "lead",
        is_consortium=False,
        categoria=categoria,
        cluster=best_cluster,
        net_worth=request.patrimony_value,
        scheduled_date=request.scheduled_date.isoformat(),
        scheduled_time=request.scheduled_time,
        duration_minutes=request.duration_minutes,
        profession=request.profissao,
        investment_interest=interest_str,
        description=request.description,
        submitted_by_email=user_email,
        opportunity_id=None,  # filled in Phase 3 after SF write succeeds
        contact_id=None,
        account_id=initial_account_id,
        sdr_salesforce_user_id=sdr_sf_id,
    )
    await session.commit()

    # ─── PHASE 2 ─────────────────────────────────────────────────────────
    # Apply the cluster-deficit (deferred commit) and run the SF partial flow.
    # If anything here fails, Phase 1's pending row remains in PG for audit.
    # FBI-2925: single-pool bands do not use weighted-deficit multi-cluster state.
    if not get_pool_spec(categoria):
        await repo.update_deficits(
            session=session,
            categoria=categoria,
            winner_cluster=best_cluster,
            cluster_weights=get_cluster_weights(categoria),
            commit=False,
        )

    loop = asyncio.get_event_loop()
    if is_account:
        contacts = (record.get("Contacts") or {}).get("records", [])
        contact_id = contacts[0]["Id"] if contacts else None
        result = await loop.run_in_executor(
            None,
            lambda: execute_r1_partial_flow_from_account(
                account_id=record["Id"],
                contact_id=contact_id,
                client_name=record.get("Name") or "Cliente",
                patrimony_value=request.patrimony_value or 0,
                patrimony_range=range_label,
                profissao=request.profissao,
                interesse_investimentos=interest_str,
                description=request.description,
                sdr_salesforce_id=sdr_sf_id,
                sdr_name=sdr_sf_name,
                sdr_email=user_email,
                placeholder_owner_id=placeholder,
                lead_source=record.get("AccountSource"),
                sf_user_connection=sf_user,
            ),
        )
        lead_id: Optional[str] = None
        account_id: Optional[str] = record["Id"]
    else:
        result = await loop.run_in_executor(
            None,
            lambda: execute_r1_partial_flow_lead(
                lead_id=initial_lead_id,
                lead_name=ld.name,
                lead_email=ld.email,
                lead_source=ld.lead_source,
                patrimony_value=request.patrimony_value or 0,
                patrimony_range=range_label,
                profissao=request.profissao,
                interesse_investimentos=interest_str,
                description=request.description,
                sdr_salesforce_id=sdr_sf_id,
                sdr_name=sdr_sf_name,
                sdr_email=user_email,
                placeholder_owner_id=placeholder,
                sf_user_connection=sf_user,
            ),
        )
        lead_id = initial_lead_id
        account_id = result.get("account_id")

    if not result.get("success"):
        # Roll back ONLY the Phase-2 deficit update (it didn't complete). The
        # Phase-1 pending row was already committed and does NOT roll back.
        # Then, in a fresh transaction, mark that row sf_error so the batch and
        # operator see a definitive SF failure (not a crash survivor).
        #
        # Best-effort, not a durable invariant: if the process dies before this
        # commit, the row stays opportunity_id NULL / processed_at NULL — which
        # is correct, reconcile_orphan_rows then treats it as a survivor and
        # repairs it on the next batch.
        await session.rollback()
        await session.execute(
            sa_text(
                f"UPDATE {_pending_d1_table()} "
                "SET processed_at = NOW(), "
                "    processed_outcome = 'sf_error', "
                "    processed_error   = :err "
                "WHERE pending_d1_routing_sk = :pid"
            ),
            {
                "pid": pending_id,
                "err": ("; ".join(result.get("errors", []) or ["unknown"]))[:500],
            },
        )
        await session.commit()
        return QualifyResponse(
            success=False,
            flow_taken="regular_d1",
            message="Falha no preparo D+1 (parcial SF)",
            lead_id=lead_id,
            account_id=account_id,
            pending_d1_id=pending_id,
            steps_completed=list(result.get("steps_completed", [])),
            errors=list(result.get("errors", [])),
            sandbox_mode=settings.sfIsSandbox,
            raw_result=result,
        )

    # ─── PHASE 3 ─────────────────────────────────────────────────────────
    # SF write succeeded. Commit the deficit + write the SF IDs back into
    # the pending row in a single transaction. If we crash here, the row
    # still exists (from Phase 1) with NULL SF IDs; the batch's
    # reconcile_orphan_rows repairs it (Lead → ConvertedOpportunityId;
    # Account → Opp by AccountId, best-effort).
    #
    # Anti-double-route guard (PR #35 / FBI-2327): a partial UNIQUE index
    # (uq_pending_d1_opportunity_unprocessed: opportunity_id WHERE
    # opportunity_id IS NOT NULL AND processed_at IS NULL) makes it
    # impossible for two un-processed rows to hold the same Opp. If a crash
    # survivor + SDR-retry race got the same Opp written onto a sibling row
    # first (directly, or via the airflow reconcile step), this UPDATE
    # raises a unique_violation. In that case the booking already landed in
    # SF and the sibling row owns the routing — so we must NOT fail the SDR.
    # We stamp THIS row 'duplicate' (excluding it from the batch) and return
    # success. The deficit rolls back with the failed tx: the sibling row is
    # the single source of the cluster debit, so dropping ours avoids a
    # double-debit for one booking.
    try:
        await session.execute(
            sa_text(
                f"UPDATE {_pending_d1_table()} "
                "SET opportunity_id = :opp, "
                "    contact_id     = :contact, "
                "    salesforce_account_id = COALESCE(salesforce_account_id, :acct) "
                "WHERE pending_d1_routing_sk = :pid"
            ),
            {
                "pid": pending_id,
                "opp": result.get("opportunity_id"),
                "contact": result.get("contact_id"),
                "acct": account_id,
            },
        )
        await session.commit()
    except IntegrityError:
        # Another un-processed row already owns this Opportunity. Drop the
        # deficit (sibling carries it) and mark this row as a duplicate so
        # the batch ignores it. The SF booking is intact; report success.
        await session.rollback()
        await session.execute(
            sa_text(
                f"UPDATE {_pending_d1_table()} "
                "SET processed_at      = NOW(), "
                "    processed_outcome = 'duplicate', "
                "    processed_error   = :err, "
                "    contact_id        = :contact, "
                "    salesforce_account_id = COALESCE(salesforce_account_id, :acct) "
                "WHERE pending_d1_routing_sk = :pid"
            ),
            {
                "pid": pending_id,
                "contact": result.get("contact_id"),
                "acct": account_id,
                "err": (
                    "duplicate opportunity_id "
                    f"{result.get('opportunity_id')} already pending; "
                    "routed by sibling row"
                )[:500],
            },
        )
        await session.commit()
        logger.warning(
            "D+1 pending row %s is a duplicate of an already-pending "
            "Opportunity %s; stamped 'duplicate', sibling row owns routing.",
            pending_id,
            result.get("opportunity_id"),
        )

    return QualifyResponse(
        success=True,
        flow_taken="regular_d1",
        message="Reserva D+1 registrada — assessor será atribuído às 21:00 BRT",
        lead_id=lead_id,
        account_id=account_id,
        contact_id=result.get("contact_id"),
        opportunity_id=result.get("opportunity_id"),
        pending_d1_id=pending_id,
        scheduled_for=(
            f"{request.scheduled_date.isoformat()}T{request.scheduled_time}:00-03:00"
        ),
        categoria=categoria,
        advisor=QualifiedAdvisor(
            full_name="(a definir — batch D+1 21:00 BRT)",
            cluster=best_cluster,
        ),
        steps_completed=list(result.get("steps_completed", [])),
        sandbox_mode=settings.sfIsSandbox,
        raw_result=result,
    )


# ── public entry point ──────────────────────────────────────────────────


# Idempotency is backed by the durable Postgres store (idempotency_store),
# keyed by (scope, user_hash, idempotency_key) in makershub._idempotency_key.
# Postgres is already a hard dependency of every request, so this adds no new
# SPOF — a DB failure propagates like any query error instead of the old Redis
# fail-closed 503. The claim survives worker restarts; orphaned claims (worker
# died mid-flight) are reclaimed after the lease via the store's reclaim path.
_IDEMPOTENCY_SCOPE = "super_r1_qualify"
_IDEMPOTENCY_RETRY_AFTER_SECONDS = 5
_TRANSIENT_ERROR_SIGNALS = ("GraphRequestError", "GraphAuthError", "GeminiServiceError")


def _is_transient_qualify_error(response: QualifyResponse) -> bool:
    return any(
        any(sig in (err or "") for sig in _TRANSIENT_ERROR_SIGNALS)
        for err in (response.errors or [])
    )


def _is_resumable_converted_lead_failure(response: QualifyResponse) -> bool:
    return bool(not response.success and response.lead_id and response.opportunity_id)


def _qualify_request_fingerprint(request: QualifyRequest, user_email: str) -> str:
    """Fingerprint of the fields that define 'the same R1 operation'. Excludes
    derived/display fields (patrimony_range, sdr_name) so a retry that omits or
    reformats them doesn't trip a false MISMATCH."""
    return idempotency_store.canonical_request_hash({
        "record_id": request.record_id,
        "service_type": request.service_type,
        "patrimony_value": request.patrimony_value,
        "scheduled_date": request.scheduled_date,
        "scheduled_time": request.scheduled_time,
        "duration_minutes": request.duration_minutes,
        "modalidade": request.modalidade,
        "description": request.description,
        "profissao": request.profissao,
        "interesse_investimentos": request.interesse_investimentos,
        "sdr_email": user_email,
        "idade": request.idade,
        "modalidade_calculo": request.modalidade_calculo,
        "id_carta": request.id_carta,
        "tomador_decisao": request.tomador_decisao,
        "intuito_consorcio": request.intuito_consorcio,
        "interesses_consorcios": request.interesses_consorcios,
    })


# Renew the claim lease every ~50s while a flow runs (store lease is 150s). A
# live worker keeps its claim fresh so a slow flow (>150s) is never reclaimed
# under it (W4); a dead worker stops renewing and the lease lapses for reclaim.
# This works even though the SF flow runs in run_in_executor: the heartbeat
# lives on the event loop, which stays free during the threaded SF calls.
_IDEMPOTENCY_HEARTBEAT_SECONDS = 50


async def _idempotency_heartbeat(
    user_email: str,
    idempotency_key: str,
    owner_token: str,
    *,
    scope: str = _IDEMPOTENCY_SCOPE,
) -> None:
    """Keep the claim lease fresh while the SF flow runs. Cancelled by qualify()
    when the flow ends; if the claim is lost (touch -> False) it stops itself."""
    while True:
        await asyncio.sleep(_IDEMPOTENCY_HEARTBEAT_SECONDS)
        try:
            alive = await idempotency_store.touch(
                scope, user_email, idempotency_key, owner_token
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("idempotency heartbeat error key=%s: %s", idempotency_key, exc)
            continue
        if not alive:
            logger.warning("idempotency heartbeat: claim lost key=%s", idempotency_key)
            return


async def _stop_heartbeat(task: Optional[asyncio.Task]) -> None:
    if task is None:
        return
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):  # noqa: BLE001
        pass


async def qualify(
    *,
    session: AsyncSession,
    current_user: dict[str, Any],
    request: QualifyRequest,
    idempotency_key: Optional[str] = None,
) -> QualifyResponse:
    """
    Single dispatcher for every Super R1 flow.

    If `idempotency_key` is supplied, the response is cached for 24h so
    AI-agent retries on transient timeouts return the original outcome
    instead of producing a duplicate Lead conversion.
    """
    user_email = (request.sdr_email or current_user.get("email") or "").strip()
    user_name_override = request.sdr_name or current_user.get("name")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Email do SDR não disponível na sessão.",
        )

    owner_token: Optional[str] = None
    if idempotency_key:
        claim = await idempotency_store.claim_or_replay(
            _IDEMPOTENCY_SCOPE, user_email, idempotency_key,
            request_hash=_qualify_request_fingerprint(request, user_email),
        )
        if claim.outcome == idempotency_store.HIT:
            replay = QualifyResponse.model_validate(claim.replay)
            logger.info(
                "qualify cache hit for user=%s key=%s flow=%s",
                user_email, idempotency_key, replay.flow_taken,
            )
            return replay
        if claim.outcome == idempotency_store.BUSY:
            logger.info("qualify idempotency=BUSY user=%s key=%s", user_email, idempotency_key)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Concurrent request with same Idempotency-Key in progress.",
                headers={"Retry-After": str(_IDEMPOTENCY_RETRY_AFTER_SECONDS)},
            )
        if claim.outcome == idempotency_store.MISMATCH:
            logger.warning(
                "qualify idempotency=MISMATCH (key reused with different payload) user=%s key=%s",
                user_email, idempotency_key,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Idempotency-Key reused with a different request payload.",
            )
        owner_token = claim.owner_token

    hb_task = (
        asyncio.create_task(
            _idempotency_heartbeat(user_email, idempotency_key, owner_token)
        )
        if owner_token else None
    )
    try:
        sf, sf_user = await _resolve_sf_connections(user_email)
        sdr_sf_id, sdr_sf_name = await _resolve_sdr_identity(sf, user_email, user_name_override)

        is_account = is_account_id(request.record_id)
        record = (
            await _fetch_account(sf, request.record_id)
            if is_account
            else await _fetch_lead(sf, request.record_id)
        )

        # Lead recordType in SF is the source of truth for consórcio routing.
        # Accounts have no consórcio recordType of their own, so SDR intent OR
        # the converting Lead's RecordType decides (FBI-2386).
        is_consorcio = _resolve_is_consorcio(
            is_account=is_account, request=request, record=record
        )
        categoria: Optional[str] = None
        if not is_consorcio:
            categoria = patrimony_to_categoria(request.patrimony_value)
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="patrimony_value inválido ou abaixo de R$ 50.000 — categoria indefinida (ver FBI-2926).",
                )

        deferred = bool(
            request.scheduled_date and is_d1_or_later(request.scheduled_date)
        )

        # Resolve which flow to take and run it (FBI-2925).
        # AMB / Mesa Hunter Investimentos paths removed.
        # Only Advisory 3 (100k-300k) may enter the D+1 batch; other bands stay sync
        # even when the meeting date is in the future.
        if is_consorcio:
            response = await _qualify_consorcio(
                request=request, sf=sf, sf_user=sf_user,
                user_email=user_email, sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name,
                session=session, is_account=is_account, record=record,
            )
        elif deferred and allows_d1_batch(categoria):
            response = await _qualify_regular_d1(
                request=request, sf=sf, sf_user=sf_user,
                user_email=user_email, sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name,
                session=session, is_account=is_account, record=record,
                categoria=categoria or "",
            )
        else:
            response = await _qualify_regular_d0(
                request=request, sf=sf, sf_user=sf_user,
                user_email=user_email, sdr_sf_id=sdr_sf_id, sdr_sf_name=sdr_sf_name,
                session=session, is_account=is_account, record=record,
                categoria=categoria or "",
            )
    except BaseException:
        await _stop_heartbeat(hb_task)
        if owner_token:
            try:
                await idempotency_store.release(
                    _IDEMPOTENCY_SCOPE, user_email, idempotency_key, owner_token
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to release qualify idempotency claim: %s", exc)
        raise

    await _stop_heartbeat(hb_task)

    # Um roteamento que falhou tem que ficar VISÍVEL (FBI-2903). O D+1 já grava a
    # falha em pending_d1_routings; o D+0 não gravava em lugar nenhum, e é
    # justamente ele que deixa Opportunity convertida sem dono e sem Event. Este
    # é o único ponto que vê o resultado final de TODOS os fluxos.
    if not response.success:
        await _record_routing_failure(
            session=session, request=request, response=response, user_email=user_email,
        )

    # Persist for replay — best-effort so a post-SF PG blip never turns a
    # successful Salesforce write into a 5xx. Transient flow errors release the
    # claim instead of caching so a retry re-runs the flow.
    if owner_token:
        try:
            # A Lead conversion commits before its post-conversion writes. If
            # those writes fail, caching the failure makes the same request
            # permanently unretryable. The retry path below reuses the linked
            # ConvertedOpportunityId and is idempotent for the R1 Event.
            resumable_converted_lead = _is_resumable_converted_lead_failure(response)
            if _is_transient_qualify_error(response) or resumable_converted_lead:
                await idempotency_store.release(
                    _IDEMPOTENCY_SCOPE, user_email, idempotency_key, owner_token
                )
            else:
                await idempotency_store.finish(
                    _IDEMPOTENCY_SCOPE, user_email, idempotency_key, owner_token,
                    response.model_dump(mode="json"),
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to persist qualify idempotency result: %s", exc)
    return response
