"""
Super R1 shared helpers — pure business logic with no DB or SF calls.

Owns the small pieces routing decisions depend on:
  - patrimony → categoria mapping (FBI-2925 matrix)
  - pool destination (dim_advisor_scd2.branch_office / position / advisor_level)
  - D+0 vs D+1 batch eligibility
  - Opportunity RecordType (Investimentos vs Financial Services)
  - record-type classification by SF id prefix
  - consórcio advisor / tier pool resolution
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field

from app.core.config import GetSettings
from app.core.financial_services import (
    LEADERSHIP_ADVISOR_LEVELS as _LEADERSHIP_ADVISOR_LEVELS,
)

# São Paulo timezone offset (UTC-3, no DST since 2019)
_SP_TZ = timezone(timedelta(hours=-3))


# ---------------------------------------------------------------------------
# FBI-2925 categorias — Investimentos PL matrix
# FBI-3482: fronteira A2/A3 revertida de 150k para 100k.
# ---------------------------------------------------------------------------

CATEGORIA_50K_100K = "50k-100k"
CATEGORIA_100K_300K = "100k-300k"
CATEGORIA_300K_5M = "300k-5M"
CATEGORIA_5M_PLUS = "5M+"

# Deprecated aliases (pre-FBI-2925). Kept for old pending rows / logs only.
CATEGORIA_BELOW_100K = "below-100k"  # deprecated — was Mesa Hunter
CATEGORIA_ABOVE_10M = "above-10M"  # deprecated — was AMB / Family Office

OPP_RT_INVESTIMENTOS = "012Kd000000qudZIAQ"  # prod fallback only; prefer SOQL
OPP_RT_FINANCIAL_SERVICES = "012U5000001Vpk1IAC"  # prod fallback only; prefer SOQL

FUNNEL_INVESTIMENTOS = "investimentos"
FUNNEL_FINANCIAL_SERVICES = "financial_services"

# Salesforce Opportunity.RecordType DeveloperName for SOQL (prod + sandbox).
# Source: SF Production Opportunity Record Types (2026-07-31).
OPP_RT_SOQL_CANDIDATES: dict[str, tuple[str, ...]] = {
    FUNNEL_INVESTIMENTOS: ("Investimentos",),
    FUNNEL_FINANCIAL_SERVICES: ("FinancialServices",),
}

# FBI-4719: RecordTypes que o Super R1 aceita reaproveitar na entrada por OPP.
# São os que ele mesmo grava (funis acima + Consórcios). Uma OPP de
# Seguros, Internacional ou Family Office teria o RecordType trocado para
# Investimentos/FS por update_opportunity_after_conversion e sairia do funil
# dela; essas seguem fora do roteamento do Super R1.
SUPER_R1_OPPORTUNITY_RECORD_TYPES: frozenset[str] = frozenset(
    {rt for rts in OPP_RT_SOQL_CANDIDATES.values() for rt in rts} | {"Consorcios"}
)


@dataclass(frozen=True)
class PoolSpec:
    """
    Destination pool on makershub.dim_advisor_scd2.

    Business `area` maps to branch_office, workbook `Posição` maps to
    position, and workbook `Level` maps to advisor_level. Team remains an
    organizational attribute and never substitutes for a level.

    `triage_level` (FBI-3491): while set, the band does NOT rotate through the
    pool. It goes entirely to the person of that level in the same area (today
    the Head of Consultoria), who redistributes each meeting by hand. Because
    that person is not the meeting's final owner, their calendar is never
    checked, the slot is not reserved (two meetings may share a slot), and the
    absence, ranking-block and Closer-fallback gates do not apply. Who holds
    the level comes from the advisor registry, never from code. Removing the
    field brings back the rotation defined by the other fields, untouched.
    """

    branch_offices: tuple[str, ...]
    position: Optional[str]
    advisor_level: Optional[str]
    min_net_worth: Optional[int]
    max_net_worth: Optional[int]
    cluster: str
    allows_d1_batch: bool
    funnel: str
    team: Optional[str] = None
    triage_level: Optional[str] = None

    @property
    def branch_office(self) -> str:
        """Primary branch_office (first of the accepted list)."""
        return self.branch_offices[0]


POOL_BY_CATEGORIA: dict[str, PoolSpec] = {
    CATEGORIA_50K_100K: PoolSpec(
        branch_offices=("Advisory",),
        position="Advisor",
        advisor_level="Advisory 2",
        min_net_worth=50_000,
        max_net_worth=100_000,
        cluster="Advisory2",
        allows_d1_batch=False,
        funnel=FUNNEL_INVESTIMENTOS,
    ),
    CATEGORIA_100K_300K: PoolSpec(
        branch_offices=("Advisory",),
        position="Advisor",
        advisor_level="Advisory 3",
        min_net_worth=100_000,
        max_net_worth=300_000,
        cluster="Advisory3",
        allows_d1_batch=True,
        funnel=FUNNEL_INVESTIMENTOS,
    ),
    CATEGORIA_300K_5M: PoolSpec(
        branch_offices=("Closer",),
        position="Closer 2",
        advisor_level=None,
        min_net_worth=300_000,
        max_net_worth=5_000_000,
        cluster="Closer",
        allows_d1_batch=False,
        funnel=FUNNEL_FINANCIAL_SERVICES,
    ),
    CATEGORIA_5M_PLUS: PoolSpec(
        branch_offices=("Consultoria",),
        position="Consultor",
        advisor_level=None,
        min_net_worth=5_000_000,
        max_net_worth=None,
        cluster="Consultoria",
        allows_d1_batch=False,
        funnel=FUNNEL_FINANCIAL_SERVICES,
        # FBI-3491: a faixa inteira vai para a Head da Consultoria, que repassa
        # à mão — foco atual da área é migrar a carteira da Assessoria. Apagar
        # esta linha devolve o rodízio entre os Consultores definido acima.
        triage_level="Head",
    ),
}

POOL_BY_CLUSTER: dict[str, PoolSpec] = {
    spec.cluster: spec for spec in POOL_BY_CATEGORIA.values()
}

# Ranking blocks ignored only by the Super R1 pool-routing consumer.  Base
# coverage measures whether an advisor is servicing their existing book; it is
# a valid distribution gate for Consultoria, but not for the acquisition pools
# Advisory2 and Closer.  Keeping the exception here (instead of deleting the
# block in the ranking producer) preserves the metric for reporting and avoids
# changing legacy routing consumers.
IGNORED_RANKING_BLOCK_TYPES_BY_CLUSTER: dict[str, frozenset[str]] = {
    "Advisory2": frozenset({"base_coverage_block"}),
    "Closer": frozenset({"base_coverage_block"}),
}

# Clusters accepted by Super R1 /availability (Investimentos path).
VALID_AVAILABILITY_CLUSTERS: frozenset[str] = frozenset(POOL_BY_CLUSTER.keys())

# Leadership levels excluded from FBI-2925 routing/availability pools.
# Reexport da fonte única (`core.financial_services`) — FBI-2976 unificou esta
# lista com a de ranking/cockpit, que estava sem 'Diretor'. Mantido aqui como
# nome importável pelos consumidores de roteamento que já apontavam para cá.
LEADERSHIP_ADVISOR_LEVELS: tuple[str, ...] = _LEADERSHIP_ADVISOR_LEVELS


# Faixas ordenadas pelo piso. FBI-3482: a régua deixou de ser uma cadeia de
# `if` com os números repetidos e passa a derivar do POOL_BY_CATEGORIA, que já
# carregava min_net_worth/max_net_worth como dado. Mudar uma faixa agora é
# mudar UM lugar.
_BANDS_BY_FLOOR: tuple[tuple[str, PoolSpec], ...] = tuple(
    sorted(POOL_BY_CATEGORIA.items(), key=lambda kv: kv[1].min_net_worth or 0)
)


def patrimony_to_categoria(patrimony_value: Optional[float]) -> Optional[str]:
    """
    Map a patrimony amount (BRL) to a Super R1 categoria (FBI-2925).

    Derives from POOL_BY_CATEGORIA (FBI-3482) — no thresholds hardcoded here.

    Returns None when patrimony is unknown, ≤0, below the matrix floor
    (floor destination is open — FBI-2926), or inside a gap between bands.

    Inclusivity: round cuts belong to the upper band — [min, max).
    """
    if patrimony_value is None:
        return None
    try:
        value = float(patrimony_value)
    except (TypeError, ValueError):
        return None
    for categoria, spec in _BANDS_BY_FLOOR:
        if value < (spec.min_net_worth or 0):
            return None
        if spec.max_net_worth is None or value < spec.max_net_worth:
            return categoria
    return None


# ---------------------------------------------------------------------------
# FBI-3482 — rótulo de faixa para HISTÓRICO
# ---------------------------------------------------------------------------
# public.stg_salesforce__routing_history não guarda a faixa: suas colunas são
# opportunity_id, owner_id, employee_id, seniority_level, routed_at,
# declared_net_worth_amount, routing_source e opportunity_type. Quem mostra
# histórico reconstrói o rótulo a partir do valor do PL — e reconstruir tudo
# com a matriz de hoje reescreve o passado: 177 oportunidades de [100k,150k)
# roteadas para Advisory 2 entre 03/08 e 09/09/2026 apareceriam sob a faixa de
# Advisory 3, com assessores de A2 listados nela.
#
# A era de cada linha é decidida pelo NÍVEL QUE RECEBEU, não por uma data de
# corte. Motivo: a data do deploy não é conhecida quando o código é escrito, e
# uma constante escrita à mão troca "reescrever o passado" por "depender de
# alguem acertar uma data" — que falha em silêncio se o deploy escorregar.
#
# O nível resolve porque a faixa que trocou de mãos tem dono único por era.
# Medido em produção em 2026-09-09, PL em [100k,150k) na série inteira:
#   Júnior 607 (26/03–01/08) · Advisory 2 177 (03/08–09/09) · Sênior 19 · Pleno 2
#   Advisory 3: ZERO.
# Logo, nessa faixa, Advisory 3 só pode ser depois do FBI-3482.
#
# Limite conhecido e aceito: onde as duas réguas se sobrepõem E mandam para o
# mesmo nível (PL < 100k, sempre Advisory 2; PL em [150k,300k), sempre
# Advisory 3), o nível não distingue a era e vale o rótulo de hoje. O pool
# exibido está certo; só o nome da faixa é o atual.

# (piso, teto, rótulo, advisor_level do pool) — fronteira A2/A3 em 150k,
# vigente de 04/08/2026 até o FBI-3482. REGISTRO HISTÓRICO, não configuração:
# atualizar esta tupla junto com a matriz viva apaga a distinção entre as eras.
PL_BANDS_FBI2925: tuple[tuple[int, Optional[int], str, Optional[str]], ...] = (
    (50_000, 150_000, "50k-150k", "Advisory 2"),
    (150_000, 300_000, "150k-300k", "Advisory 3"),
    (300_000, 5_000_000, "300k-5M", None),
    (5_000_000, None, "5M+", None),
)


def _band_at(
    bands: tuple[tuple[int, Optional[int], str, Optional[str]], ...],
    amount: int,
) -> Optional[tuple[str, Optional[str]]]:
    """(rótulo, advisor_level) da faixa que contém `amount`, ou None fora da matriz."""
    for floor, ceil, label, level in bands:
        if amount < floor:
            return None
        if ceil is None or amount < ceil:
            return label, level
    return None


def _live_bands() -> tuple[tuple[int, Optional[int], str, Optional[str]], ...]:
    return tuple(
        (spec.min_net_worth or 0, spec.max_net_worth, categoria, spec.advisor_level)
        for categoria, spec in _BANDS_BY_FLOOR
    )


def _band_decisions() -> list[tuple[int, Optional[int], Optional[str], Optional[str]]]:
    """(piso, teto, rótulo_vivo, rótulo_antigo) por intervalo entre as fronteiras
    das DUAS eras.

    É o ÚNICO lugar que decide o que cada faixa de PL pode devolver.
    `pl_band_case_sql` monta o SQL a partir disto e `pl_band_history_labels`
    declara os rótulos a partir do mesmo — foi a divergência entre esses dois
    que fez 786 linhas de histórico sumirem da tela em /routing-queue.

    `rótulo_antigo` vem preenchido SÓ quando as duas eras discordam do rótulo E
    mandam para níveis diferentes — é o único caso em que o nível gravado na
    linha distingue a era. Discordando no nome mas concordando no nível, vale o
    rótulo de hoje e o antigo NÃO entra: ele nunca seria emitido, e declará-lo
    criaria coluna sempre vazia na tela.
    """
    live = _live_bands()
    old = PL_BANDS_FBI2925
    edges = sorted({b[0] for b in live} | {b[0] for b in old}
                   | {b[1] for b in live if b[1]} | {b[1] for b in old if b[1]})

    out: list[tuple[int, Optional[int], Optional[str], Optional[str]]] = []
    for lo, hi in zip(edges, list(edges[1:]) + [None]):
        live_hit = _band_at(live, lo)
        old_hit = _band_at(old, lo)
        if live_hit is None and old_hit is None:
            out.append((lo, hi, None, None))
        elif old_hit is None or live_hit is None or live_hit[0] == old_hit[0]:
            out.append((lo, hi, (live_hit or old_hit)[0], None))
        elif live_hit[1] and old_hit[1] and live_hit[1] != old_hit[1]:
            out.append((lo, hi, live_hit[0], old_hit[0]))
        else:
            out.append((lo, hi, live_hit[0], None))
    return out


def pl_band_case_sql(amount_col: str, level_col: str) -> str:
    """
    CASE que rotula um PL com a faixa da era do próprio roteamento.

    Sem data de corte: onde as duas eras discordam do rótulo E mandam para
    níveis diferentes, quem decide é `level_col` — o nível que efetivamente
    recebeu, gravado na linha. Onde discordam mas o nível é o mesmo, vale o
    rótulo de hoje (ver o limite aceito no cabeçalho da seção).

    `amount_col` e `level_col` são identificadores de coluna, nunca entrada de
    usuário — os chamadores passam literais do próprio código.
    """
    decisoes = _band_decisions()
    floor = decisoes[0][0]
    parts = [f"WHEN {amount_col} IS NULL OR {amount_col} < {floor} THEN NULL"]

    for lo, hi, vivo, antigo in decisoes:
        if vivo is None:
            branch = "NULL"
        elif antigo is None:
            branch = f"'{vivo}'"
        else:
            nivel_vivo = _band_at(_live_bands(), lo)[1]
            branch = (
                f"CASE WHEN {level_col} = '{nivel_vivo}' THEN '{vivo}'"
                f" ELSE '{antigo}' END"
            )
        parts.append(f"ELSE {branch}" if hi is None else f"WHEN {amount_col} < {hi} THEN {branch}")

    return "CASE " + " ".join(parts) + " END"


def pl_band_history_groups() -> list[dict[str, object]]:
    """Uma entrada por faixa VIVA, dizendo quais rótulos antigos ela absorve.

    A tela do histórico mostra uma coluna por faixa viva — quatro, hoje. Mas o
    `CASE` preserva de propósito o rótulo da era anterior, e sem dizer onde ele
    entra, a linha antiga fica sem coluna e desaparece: 786 de 5.113 linhas de
    `stg_salesforce__routing_history`, medido em produção em 09/09/2026
    (reconferido em 10/09: 789 de 5.153 — o número anda com o roteamento do dia).
    A população é `routing_source = 'super-r1'` sem consórcio e PL em
    [100k, 150k), a única faixa em que as duas eras mandam para níveis
    diferentes.
    A primeira tentativa foi criar uma quinta coluna — rejeitada, quebrou o
    layout de quatro.

    O critério de absorção é o POOL, não o intervalo de PL: o rótulo antigo cai
    na coluna da faixa viva que manda para o MESMO advisor_level. Assim um
    roteamento de R$ 120 mil que foi para Advisory 2 aparece na coluna do
    Advisory 2 — e não na do Advisory 3, que é quem atende 120 mil hoje. É o que
    impede a tela de contar uma história que não aconteceu.

    A ordem das faixas vivas é preservada; quem consome monta as colunas na
    ordem em que vierem.
    """
    live = dict(_BANDS_BY_FLOOR)

    # A absorção sai da matriz congelada INTEIRA, não do que o `CASE` emite.
    # Motivo: existem DUAS fontes de rótulo no histórico, e só uma passa pelo
    # `CASE`. As linhas já roteadas são rotuladas por ele; as PENDENTES do lote
    # D+1 vêm com `category` cru de makershub._pending_d1_routing
    # (routing.py:455-484, `p.category AS categoria`). Enquanto a migration do
    # FBI-3482 não roda, essas linhas carregam '150k-300k' — rótulo que o `CASE`
    # nunca produz. Montando a absorção só pelo `CASE`, as 14 pendentes de
    # 2026-09-09 sumiam da tela, que foi como o furo apareceu.
    grupos: list[dict[str, object]] = []
    for categoria, spec in _BANDS_BY_FLOOR:
        absorve = sorted(
            label
            for _floor, _ceil, label, nivel in PL_BANDS_FBI2925
            if label not in live and nivel is not None and nivel == spec.advisor_level
        )
        grupos.append({"categoria": categoria, "absorbs": absorve})

    # Rótulo antigo sem nível (Closer/Consultoria da era anterior) não casa por
    # pool. Cai na primeira faixa viva, que é melhor que sumir, e o teste de
    # cobertura avisa se isso passar a acontecer.
    cobertos = {a for g in grupos for a in g["absorbs"]}  # type: ignore[misc]
    orfaos = [
        label for _f, _c, label, _n in PL_BANDS_FBI2925
        if label not in live and label not in cobertos
    ]
    if orfaos and grupos:
        grupos[0]["absorbs"] = sorted(list(grupos[0]["absorbs"]) + orfaos)  # type: ignore[arg-type]

    return grupos


def get_pool_spec(categoria: Optional[str]) -> Optional[PoolSpec]:
    if not categoria:
        return None
    return POOL_BY_CATEGORIA.get(categoria)


def get_pool_spec_for_cluster(cluster: Optional[str]) -> Optional[PoolSpec]:
    if not cluster:
        return None
    return POOL_BY_CLUSTER.get(cluster)


def ignored_ranking_block_types_for_cluster(
    cluster: Optional[str],
) -> frozenset[str]:
    """Ranking blocks ignored by Super R1 for one fixed pool cluster."""
    if not cluster:
        return frozenset()
    return IGNORED_RANKING_BLOCK_TYPES_BY_CLUSTER.get(cluster, frozenset())


def allows_d1_batch(categoria: Optional[str]) -> bool:
    """True only for Advisory 3 (100k-300k)."""
    spec = get_pool_spec(categoria)
    return bool(spec and spec.allows_d1_batch)


def opportunity_funnel(categoria: Optional[str]) -> Optional[str]:
    """Funnel key for Opp RecordType resolution (SOQL by DeveloperName)."""
    spec = get_pool_spec(categoria)
    return spec.funnel if spec else None


def opportunity_record_type_id(categoria: Optional[str]) -> Optional[str]:
    """
    Deprecated for runtime SF writes — prefer SOQL via opportunity_funnel +
    resolve_opportunity_record_type_id. Kept as prod-Id hint for analytics.
    """
    funnel = opportunity_funnel(categoria)
    if funnel == FUNNEL_FINANCIAL_SERVICES:
        return OPP_RT_FINANCIAL_SERVICES
    if funnel == FUNNEL_INVESTIMENTOS:
        return OPP_RT_INVESTIMENTOS
    return None


def is_mesa_hunter(categoria: Optional[str]) -> bool:
    """Deprecated (FBI-2925): Mesa Hunter below-100k removed. Always False."""
    return False


def is_amb(categoria: Optional[str]) -> bool:
    """Deprecated (FBI-2925): AMB / Family Office above-10M removed. Always False."""
    return False


def is_account_id(record_id: str) -> bool:
    if not record_id:
        return False
    return record_id.upper().startswith("001")


def is_opportunity_id(record_id: str) -> bool:
    if not record_id:
        return False
    return record_id.upper().startswith("006")


class RecordKind(str, Enum):
    """What a Super R1 `record_id` points at, decided once from its id prefix.

    One value instead of two booleans (`is_account`, `is_opportunity`) travelling
    through every dispatcher: a Lead converts, an Account and an Opportunity entry
    run the Account package (the Opportunity entry reuses its Opportunity), and the
    D+1 batch only ever sees a Lead or an Account.
    """

    LEAD = "lead"
    ACCOUNT = "account"
    OPPORTUNITY = "opportunity"

    @property
    def books_on_account(self) -> bool:
        """True when the booking runs the Account package (Account or Opportunity)."""
        return self is not RecordKind.LEAD


def classify_record_id(record_id: str) -> RecordKind:
    """`006…` = Opportunity, `001…` = Account, anything else = Lead."""
    if is_opportunity_id(record_id):
        return RecordKind.OPPORTUNITY
    if is_account_id(record_id):
        return RecordKind.ACCOUNT
    return RecordKind.LEAD


def record_type_developer_name(record: dict[str, Any]) -> Optional[str]:
    """`RecordType.DeveloperName` of a Salesforce row, or None when the row has none."""
    rt = record.get("RecordType")
    return rt.get("DeveloperName") if isinstance(rt, dict) else None


def entry_contact_id(
    opportunity: dict[str, Any], account_contacts: Sequence[dict[str, Any]],
) -> Optional[str]:
    """Contact an Opportunity entry works with (FBI-4719): the Opportunity's own,
    else the Account's oldest (the first row of its `Contacts ORDER BY CreatedDate`
    subquery). One owner for the rule: /qualify books against this contact and the
    detail screen shows its e-mail and phone."""
    return opportunity.get("ContactId") or (
        account_contacts[0].get("Id") if account_contacts else None
    )


_STAND_BY_LOSS_REASON = "Stand By"


def _lost_opportunity_refusal(opportunity: dict[str, Any], account_id: str) -> str:
    """pt-BR text for a lost Opportunity (always 409): schedule through the Account.

    The Stand By reopening date is cited only when the record already carries it
    (`DWMotivoPerda__c` = Stand By and `DWDataReaberturaStandby__c`, a text field in
    the org). The entry queries do not select those columns on purpose: the text
    is generic when they are absent."""
    opportunity_id = opportunity.get("Id")
    text = (
        f"A oportunidade {opportunity_id} está perdida e não é reaberta pelo "
        f"Super R1. Agende pela Conta {account_id}: ela abre uma nova oportunidade."
    )
    reopening = str(opportunity.get("DWDataReaberturaStandby__c") or "").strip()
    if reopening and opportunity.get("DWMotivoPerda__c") == _STAND_BY_LOSS_REASON:
        try:
            reopening = date.fromisoformat(reopening[:10]).strftime("%d/%m/%Y")
        except ValueError:
            reopening = reopening[:40]
        text += f" Ela está em Stand By, com reabertura prevista para {reopening}."
    return text


def lost_opportunity_refusal(
    opportunity: dict[str, Any], account_id: str,
) -> Optional[tuple[int, str]]:
    """(409, pt-BR text) when the Opportunity is lost, else None.

    One owner for "a lost Opportunity is never reused" (owner decision, FBI-4719):
    the entry by OPP reaches it through `opportunity_entry_refusal` and the entry by
    a converted Lead, which resumes on its Opportunity, calls it directly."""
    if opportunity.get("StageName") != "Perdida":
        return None
    return 409, _lost_opportunity_refusal(opportunity, account_id)


def opportunity_entry_refusal(opportunity: dict[str, Any]) -> Optional[tuple[int, str]]:
    """Why an Opportunity cannot enter the Super R1 (FBI-4719), or None.

    `opportunity` is the Salesforce row (IsWon, StageName, AccountId, RecordType).
    Returns (HTTP status, pt-BR message). One owner for the rule: the `/qualify`
    dispatcher refuses with it and the detail endpoint shows it to the SDR before
    the form is filled. Only an open Opportunity enters, from any campaign
    (review of PR #594); refused:

      - Won: reopening it as "Contatado" would erase the win; the Account is
        still the way to open a new cycle.
      - Lost (`StageName` = "Perdida", whatever the reason, Stand By included):
        a lost Opportunity is never reused; the Account opens a new one (owner
        decision, FBI-4719).
      - RecordType outside the Super R1: the update would switch it to
        Investimentos/FS and take it out of its own funnel (Seguros etc.).
    """
    opportunity_id = opportunity.get("Id")
    account_id = opportunity.get("AccountId")
    if opportunity.get("IsWon"):
        reopen = (
            f" Agende pela Conta {account_id} para abrir uma nova oportunidade."
            if account_id else ""
        )
        return 409, (
            f"A oportunidade {opportunity_id} está ganha e não é reaberta pelo "
            f"Super R1.{reopen}"
        )
    record_type = record_type_developer_name(opportunity)
    if record_type and record_type not in SUPER_R1_OPPORTUNITY_RECORD_TYPES:
        return 422, (
            f"Oportunidade do tipo {record_type} não é roteada pelo Super R1 "
            f"(aceita: {', '.join(sorted(SUPER_R1_OPPORTUNITY_RECORD_TYPES))})."
        )
    if not account_id:
        return 409, (
            f"Oportunidade {opportunity_id} sem Conta vinculada; acione o suporte."
        )
    return lost_opportunity_refusal(opportunity, account_id)


def today_brt() -> date:
    return datetime.now(_SP_TZ).date()


def is_d1_or_later(scheduled_date: str | date) -> bool:
    if isinstance(scheduled_date, date):
        d = scheduled_date
    else:
        try:
            d = date.fromisoformat(scheduled_date)
        except ValueError:
            return False
    return d > today_brt()


class ConsorcioAdvisor(BaseModel):
    """Identity of the single advisor every consórcio lead is routed to."""
    email: str = Field(description="Corporate email of the consórcio advisor")
    sf_id: str = Field(description="Salesforce User Id (005…)")
    name: str = Field(description="Display name shown in the FE")


_CONSORCIO_UNCONFIGURED = (
    "Assessor de consórcio não configurado: defina o assessor fixo em "
    "Gerenciamento → Config Super R1 (ou, como fallback, CONSORCIO_ADVISOR_EMAIL, "
    "CONSORCIO_ADVISOR_SF_ID e CONSORCIO_ADVISOR_NAME no env do backend)."
)


class ConsorcioConfig(BaseModel):
    """
    Consórcio routing configuration, already parsed and normalized.

    One shape for both sources: the admin page writes it to the database and the
    env is the fallback, so the resolution algorithm below never has to know
    where the values came from. Override keys are lowercased SDR emails.
    """
    fixed: Optional[ConsorcioAdvisor] = None
    overrides: dict[str, ConsorcioAdvisor] = Field(default_factory=dict)
    pools: dict[str, list[ConsorcioAdvisor]] = Field(default_factory=dict)

    def override_for(self, sdr_email: Optional[str]) -> Optional[ConsorcioAdvisor]:
        if not sdr_email:
            return None
        return self.overrides.get(sdr_email.strip().lower())


def _advisor_from_dict(raw: Any) -> Optional[ConsorcioAdvisor]:
    """A pool/override entry as an advisor, or None when it's incomplete."""
    if not isinstance(raw, dict):
        return None
    email = raw.get("email")
    sf_id = raw.get("sfId") or raw.get("sf_id")
    name = raw.get("name")
    if email and sf_id and name:
        return ConsorcioAdvisor(email=email, sf_id=sf_id, name=name)
    return None


def consorcio_config_from_env() -> ConsorcioConfig:
    """
    The env-var view of the consórcio config — the fallback used whenever the
    database has nothing set for a given piece.
    """
    import json
    import logging

    s = GetSettings()
    log = logging.getLogger(__name__)

    fixed = None
    if s.consorcioAdvisorEmail and s.consorcioAdvisorSfId and s.consorcioAdvisorName:
        fixed = ConsorcioAdvisor(
            email=s.consorcioAdvisorEmail,
            sf_id=s.consorcioAdvisorSfId,
            name=s.consorcioAdvisorName,
        )

    overrides: dict[str, ConsorcioAdvisor] = {}
    if s.consorcioSdrOverrides:
        try:
            raw = json.loads(s.consorcioSdrOverrides)
        except (json.JSONDecodeError, ValueError):
            log.warning("CONSORCIO_SDR_OVERRIDES is not valid JSON; using default advisor")
            raw = {}
        if isinstance(raw, dict):
            for sdr, entry in raw.items():
                merged = _merge_override(entry, fixed)
                if merged is not None:
                    overrides[str(sdr).strip().lower()] = merged

    pools: dict[str, list[ConsorcioAdvisor]] = {}
    if s.consorcioPools:
        try:
            raw_pools = json.loads(s.consorcioPools)
        except (json.JSONDecodeError, ValueError):
            log.warning("CONSORCIO_POOLS is not valid JSON; using fixed advisor")
            raw_pools = {}
        if isinstance(raw_pools, dict):
            for tier, entries in raw_pools.items():
                if not isinstance(entries, list):
                    continue
                members = [a for a in (_advisor_from_dict(e) for e in entries) if a]
                if members:
                    pools[str(tier)] = members

    return ConsorcioConfig(fixed=fixed, overrides=overrides, pools=pools)


def _merge_override(entry: Any, fixed: Optional[ConsorcioAdvisor]) -> Optional[ConsorcioAdvisor]:
    """An override entry, with any missing field inherited from the fixed advisor."""
    if not isinstance(entry, dict):
        return None
    email = entry.get("email") or (fixed.email if fixed else None)
    sf_id = entry.get("sfId") or entry.get("sf_id") or (fixed.sf_id if fixed else None)
    name = entry.get("name") or (fixed.name if fixed else None)
    if email and sf_id and name:
        return ConsorcioAdvisor(email=email, sf_id=sf_id, name=name)
    return None


def _consorcio_sdr_override_entry(sdr_email: Optional[str]) -> Optional[dict]:
    """
    The raw `CONSORCIO_SDR_OVERRIDES` entry for this SDR, or None when the SDR
    has no override (no config, SDR not listed, or invalid JSON — logged).
    Being listed means the SDR has a dedicated consórcio partner.
    """
    import json
    import logging

    s = GetSettings()
    if not sdr_email or not s.consorcioSdrOverrides:
        return None

    try:
        overrides = json.loads(s.consorcioSdrOverrides)
    except (json.JSONDecodeError, ValueError):
        logging.getLogger(__name__).warning(
            "CONSORCIO_SDR_OVERRIDES is not valid JSON; using default advisor"
        )
        return None

    if not isinstance(overrides, dict):
        return None

    entry = overrides.get(sdr_email.strip().lower())
    return entry if isinstance(entry, dict) else None


def _consorcio_advisor_from_entry(entry: Optional[dict]) -> ConsorcioAdvisor:
    """
    Build the consórcio advisor from the fixed `CONSORCIO_ADVISOR_*` env vars,
    merged with a pre-parsed `CONSORCIO_SDR_OVERRIDES` entry (or None).
    Takes the entry instead of the SDR email so callers that already resolved
    the entry don't parse the overrides JSON twice.

    Raises ValueError when the default isn't configured.
    """
    s = GetSettings()
    if not s.consorcioAdvisorEmail or not s.consorcioAdvisorSfId or not s.consorcioAdvisorName:
        raise ValueError(_CONSORCIO_UNCONFIGURED)
    default = ConsorcioAdvisor(
        email=s.consorcioAdvisorEmail,
        sf_id=s.consorcioAdvisorSfId,
        name=s.consorcioAdvisorName,
    )

    if entry is None:
        return default

    email = entry.get("email") or default.email
    sf_id = entry.get("sfId") or entry.get("sf_id") or default.sf_id
    name = entry.get("name") or default.name
    return ConsorcioAdvisor(email=email, sf_id=sf_id, name=name)


def get_consorcio_advisor(
    sdr_email: Optional[str] = None, config: Optional["ConsorcioConfig"] = None
) -> ConsorcioAdvisor:
    """
    Resolve the consórcio advisor for a given SDR.

    Default: the single fixed advisor. Override: a per-SDR entry routes that
    SDR's consórcio bookings to an alternate advisor — used when an SDR has a
    dedicated consórcio partner instead of the default specialist.

    `config` comes from the database when the admin page has it set; omitting it
    reads the env, which is the fallback. Raises ValueError when the fixed
    advisor isn't configured anywhere.
    """
    if config is None:
        return _consorcio_advisor_from_entry(_consorcio_sdr_override_entry(sdr_email))
    entry = config.override_for(sdr_email)
    if entry is not None:
        return entry
    if config.fixed is None:
        raise ValueError(_CONSORCIO_UNCONFIGURED)
    return config.fixed


# Consórcio PL tiers (FBI-2387). Above the fixed-advisor era: 300k+ and 1MM+
# route to dedicated PJ-Consórcio pools; below 300k stays on the fixed advisor.
CONSORCIO_TIER_1MM = "1MM+"   # PL >= R$ 1.000.000
CONSORCIO_TIER_300K = "300k+"  # R$ 300.000 <= PL < R$ 1.000.000


def consorcio_tier(patrimony_value: Optional[float]) -> Optional[str]:
    """
    Map a patrimony amount to a consórcio routing tier, or None when PL < 300k
    (which keeps the fixed advisor). Mirrors patrimony_to_categoria's thresholds:
    300k+ = [300k, 1M); 1MM+ = [1M, ∞).
    """
    if patrimony_value is None:
        return None
    try:
        value = float(patrimony_value)
    except (TypeError, ValueError):
        return None
    if value >= 1_000_000:
        return CONSORCIO_TIER_1MM
    if value >= 300_000:
        return CONSORCIO_TIER_300K
    return None


class ConsorcioPoolResolution(BaseModel):
    """
    Outcome of resolving the consórcio pool, with its origin made explicit so
    callers can log/decide on "tier pool actually in use" without proxies like
    `len(advisors) > 1` (a 1-entry tier pool IS a pool in use — FBI-2436).
    """
    advisors: list[ConsorcioAdvisor]
    source: str = Field(description="'override' | 'tier_pool' | 'fixed'")
    tier: Optional[str] = Field(default=None, description="'1MM+' | '300k+' | None")


def resolve_consorcio_pool(
    patrimony_value: Optional[float],
    sdr_email: Optional[str] = None,
    config: Optional[ConsorcioConfig] = None,
) -> ConsorcioPoolResolution:
    """
    Resolve the consórcio advisor pool for a lead's patrimony (FBI-2387).

    Precedence (FBI-2397): an SDR with a per-SDR override has a dedicated
    consórcio partner and ALWAYS gets that advisor, at any PL — activating the
    tier pools must not silently reroute those SDRs. Then PL >= 1MM and 300k+
    return the configured tier pool; PL < 300k — or any tier with no config —
    falls back to the single fixed advisor.

    `config` is the database-backed configuration written by the admin page; when
    omitted the env is read instead, which is the fallback. Raises ValueError
    only when a fixed advisor is needed and none is configured in either source.
    """
    cfg = config if config is not None else consorcio_config_from_env()
    tier = consorcio_tier(patrimony_value)

    override = cfg.override_for(sdr_email)
    if override is not None:
        return ConsorcioPoolResolution(advisors=[override], source="override", tier=tier)

    if tier is not None:
        pool = cfg.pools.get(tier) or []
        if pool:
            return ConsorcioPoolResolution(advisors=pool, source="tier_pool", tier=tier)

    if cfg.fixed is None:
        raise ValueError(_CONSORCIO_UNCONFIGURED)
    return ConsorcioPoolResolution(advisors=[cfg.fixed], source="fixed", tier=tier)


def get_consorcio_pool(
    patrimony_value: Optional[float],
    sdr_email: Optional[str] = None,
    config: Optional[ConsorcioConfig] = None,
) -> list[ConsorcioAdvisor]:
    """Advisor list of resolve_consorcio_pool — kept for existing call sites."""
    return resolve_consorcio_pool(patrimony_value, sdr_email, config).advisors
