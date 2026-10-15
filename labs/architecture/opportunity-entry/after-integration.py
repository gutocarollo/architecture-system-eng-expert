"""
Integração com Salesforce para sincronização de colaboradores e fluxo R1.
Adaptado de governance-module/utils/salesforce_export.py para FastAPI.
"""
import base64
import os
import logging
import re
import string
import random
import time
import requests
import defusedxml.ElementTree as SafeET
from xml.sax.saxutils import escape as _xml_escape
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.r1_meeting import MEETING_DURATION
from app.core.timezone import add_real_minutes
from app.core.org_vocabulary import canonical_index, vocab_key
from app.integrations.eligibility import (
    should_have_partner_user,
    resolve_salesforce_profile_name,
    role_is_explicit_partner,
)
from app.integrations.salesforce_team_contract import (
    PARTNER_ACCOUNT_NAMES,
    SHARING_FIELD,
    derive_dwteam_token,
)
from app.integrations import salesforce_field_contract as field_contract

_SF_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{15,18}$')


def _validate_sf_id(sf_id: str) -> str:
    if not _SF_ID_PATTERN.match(sf_id):
        raise ValueError(f"Invalid Salesforce ID format: {sf_id}")
    return sf_id


def _esc_soql(value: str) -> str:
    """Escapa string p/ interpolação em SOQL (defesa em profundidade — Fase 3.6)."""
    return str(value).replace('\\', '\\\\').replace("'", "\\'")


# Marca que o NOSSO código carimba no Username ao converter licença interna em
# licença de portal. Ela tem dois leitores de propósito:
#   * `reconcile_salesforce_access_role` escreve ao estacionar a conta antiga;
#   * `resolve_salesforce_identities` lê para ignorar a conta que ele mesmo
#     aposentou.
# Constante única porque se as duas pontas divergirem a conversão volta a se
# auto-bloquear, e o sintoma aparece meses depois, longe da causa.
STANDARD_MIGRATED_MARKER = '.standard-migrated.'


def _park_email(email: str, stamp: int) -> str:
    """Endereço estacionado da conta que a conversão aposenta.

    Usa a forma `+tag` para continuar sendo um e-mail válido — o Salesforce
    recusa o campo mal formado, e um endereço ilegível esconderia de quem
    audita o org de quem era aquela conta.
    """
    texto = str(email or '').strip()
    if '@' not in texto:
        return texto
    local, _, dominio = texto.partition('@')
    return f"{local}+standard-migrated-{stamp}@{dominio}"


def _is_parked_leftover(record: Dict[str, Any]) -> bool:
    """A conta é sobra de uma conversão NOSSA, já aposentada?

    Exigir INATIVA é o ponto da regra, não detalhe. Conta marcada e ainda ATIVA
    significa conversão que quebrou no meio: ignorá-la faria o resolvedor dizer
    `none`, e o sistema criaria uma segunda conta — exatamente a duplicata que
    ele existe para impedir. Marcada-e-ativa continua sendo caso de gente.
    """
    if record.get('IsActive'):
        return False
    return STANDARD_MIGRATED_MARKER in str(record.get('Username') or '')


def resolve_salesforce_identities(
    sf: Any,
    contact_id: Optional[str],
    email: str,
    ignore_user_ids: Optional[Any] = None,
) -> Dict[str, Any]:
    """Read-only identity resolution before any Contact/User write.

    The same person can be discoverable by several Salesforce identifiers.  A
    single distinct active PowerPartner is safe to reuse; every other match is
    deliberately returned for manual handling instead of manufacturing another
    identity.

    `ignore_user_ids` existe para o caminho de CONVERSÃO. Ao trocar licença
    interna por licença de portal, `reconcile_salesforce_access_role` estaciona
    Username, FederationIdentifier E Email da conta antiga. Ainda assim o Id
    precisa ser ignorado: entre estacionar e criar, a conta de origem continua
    existindo e casaria por outros predicados.

    No Salesforce o USERNAME é único no mundo; o Email NÃO é — duas contas
    podem compartilhá-lo. Foi justamente por isso que estacionar só o Username
    deixava a conta aposentada disputando identidade com a nova, e a pessoa
    terminava em `ambiguous` depois de uma conversão bem-sucedida. Medido em
    2026-09-10: 22 dos 24 Users Standard ativos com e-mail @fazcapital têm
    Email igual ao Username, então isso atingia praticamente toda conversão.

    Ignorar aqui NÃO afrouxa o invariante contra duplicata: o Id ignorado é o
    da conta que o chamador já leu, já decidiu converter e vai desativar em
    seguida. Qualquer OUTRA identidade continua bloqueando.
    """
    ignorados = {
        str(uid).strip()
        for uid in (
            [ignore_user_ids] if isinstance(ignore_user_ids, str)
            else (ignore_user_ids or [])
        )
        if str(uid).strip()
    }
    lookups = []
    if contact_id:
        lookups.append(f"ContactId = '{_validate_sf_id(str(contact_id))}'")
    escaped_email = _esc_soql(email)
    lookups.extend((
        f"Username = '{escaped_email}'",
        f"Email = '{escaped_email}'",
        f"FederationIdentifier = '{escaped_email}'",
    ))
    users: Dict[str, Dict[str, Any]] = {}
    fields = 'Id, ContactId, Username, Email, FederationIdentifier, IsActive, IsPortalEnabled, UserType'
    for predicate in lookups:
        result = sf.query(f"SELECT {fields} FROM User WHERE {predicate}")
        for record in result.get('records') or []:
            identificador = str(record.get('Id') or '').strip()
            if not identificador or identificador in ignorados:
                continue
            # Sobra de conversão nossa não disputa identidade: ela está inativa,
            # não consome licença e não dá acesso. Sem isto, quando a conta
            # aposentada carrega o ContactId consultado, ela soma-se à conta
            # viva e a pessoa cai em `ambiguous` para sempre. O Email já não
            # casa desde 354b49071 (2026-09-10, 13:44), que o estaciona junto;
            # o ContactId, que o estacionamento não toca, é o predicado que
            # resta. (O mecanismo ORIGINAL era o Email: antes daquela hora,
            # TODA conversão bem-sucedida congelava a pessoa em `ambiguous`.)
            if _is_parked_leftover(record):
                continue
            users[identificador] = record

    records = list(users.values())
    if not records:
        return {'status': 'none', 'records': []}

    # GAP ACEITO (Bruno, 2026-09-10): as 9 identidades ambíguas de hoje ficam
    # como estão, e a automação segue parada para elas. Não é descuido nem
    # pendência — é decisão, tomada com a lista na mesa.
    #
    # Medido em salesforce_prod.stg_salesforce__user: 9 e-mails @fazcapital com
    # 2+ contas. Seis são de gente ativa (Jullya Bitencourt, Samuel Silva
    # Santos, Pedro Wolfart, Renato Tubino, Robert Fernandes e Júlio Balena) e
    # três de desligados (Vitória Luiza, Samuel Braga, Artur Costa).
    #
    # Custo real, para quem for reavaliar: só o Júlio consome licença a mais —
    # ele tem TRÊS contas internas ativas. Nos outros cinco ativos a duplicata
    # está desativada, então não gasta licença; nos três desligados as duas
    # contas estão desativadas, que é o correto. O preço do gap é a automação
    # de Salesforce ficar parada para essas 9 pessoas, não dinheiro.
    #
    # Consertar exige decisão humana caso a caso — qual conta é a boa —, e é o
    # que a cláusula do pedido original manda fazer com identidade ambígua.
    # NÃO transformar isto em resolução automática sem uma decisão nova: o
    # único afrouxamento autorizado é o de `_is_parked_leftover`, que ignora
    # apenas a sobra que este mesmo módulo produziu.
    if len(records) != 1:
        return {'status': 'ambiguous', 'records': records}
    record = records[0]
    if not record.get('IsActive', False):
        return {'status': 'inactive', 'record': record}
    if record.get('UserType') != 'PowerPartner':
        return {'status': 'standard_or_other', 'record': record}
    return {'status': 'active_partner', 'record': record}


def _parse_sf_datetime(value: str) -> datetime:
    """Parse Salesforce ISO timestamps and normalize them to aware UTC."""
    normalized = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError(f"Salesforce datetime has no timezone: {value}")
    return parsed.astimezone(timezone.utc)
from dotenv import load_dotenv
from simple_salesforce.api import Salesforce
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import URL, create_engine, text
from sqlalchemy.pool import NullPool
from app.integrations.teams_notifications import (
    notify_teams_salesforce_error,
    send_teams_notification_ramal_assigned,
)

load_dotenv()

logger = logging.getLogger(__name__)

# Salesforce connection cache (TTL 55 min — just under SF's 2-hour token lifetime)
# This avoids re-authenticating on every call while still refreshing well before expiry.
SF_CONNECTION_TTL_SECONDS = 55 * 60  # 55 minutes

# Teto da janela de Users por email em `resolve_sf_user_by_email`.
#
# Pior colisão real medida em `salesforce_prod.stg_salesforce__user` (2026-07-31):
# 3 Users ATIVOS no mesmo email (julio.balena@fazcapital.com.br) e ZERO emails
# com mais de 5. Então 5 cobre com folga — o risco não é o número, é o modo de
# falha: passar do teto empurra o User canônico para fora da janela e degrada o
# resultado para o ramo de fallback SEM sinal nenhum. Constante nomeada para que
# o log de canário e o teste falem do mesmo número.
_EMAIL_MATCH_LIMIT = 5
_sf_connection_cache: Dict[str, Any] = {"conn": None, "expires": 0}

# Per-user JWT connection cache: { "email": { "conn": Salesforce, "expires": float } }
_sf_user_connection_cache: Dict[str, Dict[str, Any]] = {}

# Single-flight locks: concurrent cache misses for the same user share one auth
# round-trip instead of all hitting Salesforce.
import threading
_sf_admin_auth_lock = threading.Lock()
_sf_user_auth_locks: Dict[str, threading.Lock] = {}
_sf_user_auth_locks_master = threading.Lock()

# Salesforce HTTP timeout. simple_salesforce's requests have no default timeout,
# so a hung SF call would pin a run_in_executor thread until gunicorn's 120s.
# Mirror NextBilling's 30s. Applied via a session that defaults `timeout` on
# every request (auth, SOQL, DML).
SF_HTTP_TIMEOUT_SECONDS = float(os.getenv("SF_HTTP_TIMEOUT_SECONDS", "30"))


class _TimeoutSession(requests.Session):
    """requests.Session that applies a default timeout to every request."""

    def __init__(self, timeout: float):
        super().__init__()
        self._timeout = timeout

    def request(self, *args, **kwargs):  # type: ignore[override]
        kwargs.setdefault("timeout", self._timeout)
        return super().request(*args, **kwargs)


def _sf_timeout_session() -> requests.Session:
    return _TimeoutSession(SF_HTTP_TIMEOUT_SECONDS)


def _get_user_auth_lock(cache_key: str) -> threading.Lock:
    with _sf_user_auth_locks_master:
        lock = _sf_user_auth_locks.get(cache_key)
        if lock is None:
            lock = threading.Lock()
            _sf_user_auth_locks[cache_key] = lock
        return lock

# Org-specific ID resolution cache — IDs differ between production and sandbox.
# Resolved dynamically by querying Salesforce by name/email so that switching
# SF_IS_SANDBOX requires zero ID changes.  Invalidated with the admin connection.
_resolved_org_ids: Dict[str, str] = {}

# Per-email "can this user make API calls?" cache: { email: {value: bool, expires: float} }.
# A portal user whose profile/permission set lacks "API Enabled" can still mint a JWT
# session, but every REST data call returns API_CURRENTLY_DISABLED. We pre-check so the
# R1 write path can route around it (write as admin) instead of failing the conversion.
_user_api_access_cache: Dict[str, Dict[str, Any]] = {}


def _invalidate_org_ids() -> None:
    """Clear cached org-specific Salesforce IDs."""
    _resolved_org_ids.clear()
    _user_api_access_cache.clear()


def _invalidate_admin_cache() -> None:
    """Force the admin connection to re-authenticate on next call."""
    _sf_connection_cache["conn"] = None
    _sf_connection_cache["expires"] = 0
    _invalidate_org_ids()


def _invalidate_user_cache(user_email: str) -> None:
    """Force a specific user connection to re-authenticate on next call."""
    _sf_user_connection_cache.pop(user_email, None)


def get_fresh_admin_connection() -> Optional[Salesforce]:
    """Get admin connection, forcing re-auth if the current one is expired."""
    _invalidate_admin_cache()
    return get_salesforce_connection()


def get_fresh_user_connection(user_email: str) -> Optional[Salesforce]:
    """Get per-user connection, forcing re-auth if the current one is expired."""
    _invalidate_user_cache(user_email)
    return get_salesforce_connection_as_user(user_email)


def send_teams_notification(name: str, device_id: int,
                            phone_extension: str) -> bool:
    """
    Envia notificação ao Teams quando um ramal é atribuído a um colaborador.

    Args:
        name: Nome do colaborador
        device_id: ID do dispositivo
        phone_extension: Número do ramal

    Returns:
        True se a notificação foi enviada com sucesso, False caso contrário
    """
    try:
        logger.info(
            "Sending Teams notification for ramal assignment: name=%s device_id=%s extension=%s",
            name,
            device_id,
            phone_extension,
        )
        return send_teams_notification_ramal_assigned(
            name=name,
            device_id=device_id,
            phone_extension=phone_extension,
        )
    except Exception:
        logger.error("Failed to send Teams notification", exc_info=True)
        return False


# Salesforce Account IDs (constants)
FAZ_CAPITAL_ACCOUNT_ID = "001DQ00000D0ZVeYAN"
FAZ_CAPITAL_SDR_ACCOUNT_ID = "001U500000Lr2KaIAJ"  # Faz Capital - Team SDR (para team='Prospecção')

# Profile IDs — fallback LEGADO apenas; a resolução canônica é por NAME via
# get_profile_id_by_name (Fase 1, 2026-07-01). Motivo: o hardcode de
# PROFILE_SDR_ID ficou ERRADO ('...DjXunIAF' ≠ live '...DjXutIAF') por tempo
# indeterminado e só não quebrava porque get_profile_ids() sobrescrevia no
# caminho de criação — o caminho de reativação usava o valor podre.
PROFILE_ASSESSOR_ID = "00eU500000DjXusIAF"  # Portal - Assessor
PROFILE_SDR_ID = "00eU500000DjXutIAF"  # Portal - SDR (corrigido 2026-07-01)

# Cache de Profile Name -> Id resolvido live (por processo)
_PROFILE_ID_CACHE: Dict[str, str] = {}


def get_profile_id_by_name(sf: Salesforce, profile_name: str) -> Optional[str]:
    """Resolve o Id de um Profile pelo Name, com cache por processo.

    Fonte única de IDs de profile (Fase 1): nomes vêm de
    eligibility.resolve_salesforce_profile_name; nunca confiar em hardcode.
    """
    if not profile_name:
        return None
    cached = _PROFILE_ID_CACHE.get(profile_name)
    if cached:
        return cached
    try:
        safe_name = _esc_soql(profile_name)
        result = sf.query(f"SELECT Id FROM Profile WHERE Name = '{safe_name}'")
        if result.get('totalSize', 0) > 0:
            profile_id = result['records'][0]['Id']
            _PROFILE_ID_CACHE[profile_name] = profile_id
            return profile_id
        logger.error("Profile '%s' não encontrado no Salesforce", profile_name)
        return None
    except Exception as e:
        logger.error("Erro ao resolver Profile '%s': %s", profile_name, e)
        return None


def _extract_sf_error_code(exc: Exception) -> Optional[str]:
    """Extrai o errorCode estruturado de exceções do simple-salesforce.

    LICENSE_LIMIT_EXCEEDED / DUPLICATE_USERNAME / FIELD_INTEGRITY_EXCEPTION etc.
    Antes disto, toda falha colapsava em None genérico e o chamador não
    distinguia licença esgotada de timeout (gap B1 do relatório).
    """
    content = getattr(exc, 'content', None)
    if isinstance(content, list) and content and isinstance(content[0], dict):
        code = content[0].get('errorCode')
        if code:
            return str(code)
    text_repr = str(exc)
    for known in ('CANNOT_UPDATE_CONVERTED_LEAD', 'LICENSE_LIMIT_EXCEEDED',
                  'DUPLICATE_USERNAME',
                  'DUPLICATES_DETECTED', 'FIELD_INTEGRITY_EXCEPTION',
                  'INVALID_CROSS_REFERENCE_KEY', 'INSUFFICIENT_ACCESS',
                  'REQUIRED_FIELD_MISSING', 'UNABLE_TO_LOCK_ROW'):
        if re.search(rf"(?<!\w){re.escape(known)}(?!\w)", text_repr):
            return known
    return None


# FBI-3061 (D4=Opção C, AM10 §14.3): fonte única do classificador de erro de
# SESSÃO do operador, promovida de call_list_service.py:80-121 (FBI-2733,
# commit 98aae5120). Consome _extract_sf_error_code acima em vez de duplicar
# a extração estruturada de content[0]['errorCode'] — só a tupla fechada e os
# marcadores textuais são próprios daqui.
SF_USER_FALLBACK_ERROR_CODES: tuple[str, ...] = (
    "invalid_field_for_insert_update",
    "insufficient_access_on_cross_reference_entity",
)

_SF_USER_ACCESS_ERROR_MARKERS = (
    "unable to create/update fields",
)


def is_sf_user_access_error(error: Any) -> bool:
    """True quando o erro do SF é negação de acesso da SESSÃO do operador —
    isto é, retentar sob a conexão admin tem chance real de passar.

    Reconhece 3 formas (o 4º ramo original, específico de
    `dwclientcallid__c`/call-list, foi PODADO daqui e permanece em
    call_list_service.py como wrapper — não faz sentido em Opportunity.create):
      1. errorCode estruturado (content[0]['errorCode']) — via
         _extract_sf_error_code, ramo :233-237.
      2. errorCode serializado como string (dict/repr gravado em texto).
      3. marcador textual solto (ex.: "unable to create/update fields").
    """
    code = _extract_sf_error_code(error)
    if code:
        return code.lower() in SF_USER_FALLBACK_ERROR_CODES

    lowered = str(error).lower()
    has_exact_fallback_code = any(
        lowered == fallback_code
        or lowered.startswith(f"{fallback_code}:")
        or f"'errorcode': '{fallback_code}'" in lowered
        or f'"errorcode": "{fallback_code}"' in lowered
        for fallback_code in SF_USER_FALLBACK_ERROR_CODES
    )
    return has_exact_fallback_code or any(
        marker in lowered for marker in _SF_USER_ACCESS_ERROR_MARKERS
    )


# Team to Salesforce Account Mapping
# Baseado nas Accounts "Faz Capital - Team {Nome}" no Salesforce
# IMPORTANTE: Estes IDs devem corresponder EXATAMENTE aos do Streamlit
#
# O mapa é consultado no time de DESTINO (update_contact_account e a criação
# do Contact). Estar aqui significa "este time é destino válido", não "as
# pessoas deste time são mantidas": o sync de DWTeam__c/DWRamal__c não usa
# lista nenhuma. Por isso o mapa é ADITIVO — chave nunca sai, mesmo sem
# pessoa (decisão D[3], 2026-09-03): remover uma chave só faria a próxima
# troca PARA aquele time falhar em silêncio.
#
# Taxonomia de 2026-08-02 (FBI-2957): as 8 chaves de Banking/Advisory/
# Consultoria/Closer foram adicionadas em 2026-09-04 depois de um mês em que
# 79 Contacts precisaram ser movidos à mão no Salesforce. Ids conferidos
# contra salesforce_prod.stg_salesforce__account (Name exato) e validados
# pelo checksum de 18 caracteres em tests/unit/test_team_account_mapping.py.
TEAM_TO_SALESFORCE_ACCOUNT_MAPPING = {
    # Times de Assessoria (taxonomia antiga; sem pessoa desde 2026-08-02,
    # mantidos por serem destino válido)
    'Manhattan': '001U500000Lr2W2IAJ',  # Faz Capital - Team Manhattan
    'Miami': '001U500000Lr4kbIAB',  # Faz Capital - Team Miami
    'Monaco': '001U500000LqxZQIAZ',  # Faz Capital - Team Monaco
    'Pelotas': '001U500000LrAI5IAN',  # Faz Capital - Team Pelotas
    'Tokyo': '001U500000Lqr7cIAB',  # Faz Capital - Team Tokyo
    # Vitória: até 2026-09-04 o Id tinha 17 caracteres ('001U500000LrvcIAB',
    # faltava o 'q') e não existia na org — toda troca PARA Vitória falhava.
    'Vitória': '001U500000LqrvcIAB',  # Faz Capital - Team Vitória
    'Zurich': '001U500000LrAMvIAN',  # Faz Capital - Team Zurich

    # Banking (taxonomia 2026-08-02)
    'Genebra': '001U500000v0TKgIAM',  # Faz Capital - Team Genebra
    'Madrid': '001U500000v0qx4IAA',  # Faz Capital - Team Madrid
    'Dallas': '001U500000v0bwUIAQ',  # Faz Capital - Team Dallas

    # Advisory (taxonomia 2026-08-02)
    'Advisory 1': '001U500000v2Fv7IAE',  # Faz Capital - Team Advisory 1
    'Advisory 2': '001U500000v2b2fIAA',  # Faz Capital - Team Advisory 2
    'Advisory 3': '001U500000v1q8gIAA',  # Faz Capital - Team Advisory 3

    # Consultoria e Closer (taxonomia 2026-08-02)
    'Consultoria': '001U500000v0afRIAQ',  # Faz Capital - Team Consultoria
    'Closer': '001U500000v0RfNIAU',  # Faz Capital - Team Closer

    # Times Digitais
    'Mesa Digital Hunter': '001U500000QAMWgIAP',  # Faz Capital - Team Hunter
    'Mesa Digital Farmer': '001U500000QAeoWIAT',  # Faz Capital - Team Farmer
    'Mesa Digital': '001U500000OLiTFIA1',  # Faz Capital - Team Digital

    # Time Prospecção/SDR
    'Prospecção': '001U500000Lr2KaIAJ',  # Faz Capital - Team SDR

    # Outros times
    'Seguros': '001U500000Lr9IpIAJ',  # Faz Capital - Team Seguros
    # FBI-4842: nomes canônicos usados no cadastro desde 2026-10-06. São o MESMO
    # destino dos rótulos legados logo abaixo (que ficam por serem destino válido
    # para quem ainda os carrega, ex.: Mayara em 'XP Internacional').
    'Consórcio': '001U500000LqrfWIAR',  # Faz Capital - PJ Consórcio
    'Offshore': '001U500000O9xz8IAB',  # Faz Consulting - Team Offshore
    'PJ Consórcio': '001U500000LqrfWIAR',  # Faz Capital - PJ Consórcio
    'XP Internacional':
    '001U500000O9xz8IAB',  # Faz Consulting - Team Offshore (mapeamento aproximado)
    'Investors': '001U500000PSxpzIAD',  # Faz Capital - Team Investors

    # FBI-4842 (2026-10-06): partner Accounts that existed without a key. Without
    # the key, moving someone TO these teams ended in "role preserved" without
    # changing anything (PJ had 4 active people in the register).
    'PJ': '001U500000iM8qVIAS',  # Faz Capital - Pessoa Jurídica
    'Mato Grosso': '001U500000v9nTjIAI',  # Faz Capital - Team Mato Grosso
    'Monte Carlo': '001U500000v0d5PIAQ',  # Faz Capital - Team Monte Carlo
}

# `chave de comparação -> Account Id`, derivado do mapa acima (não há segunda
# lista). Importar o módulo falha se duas chaves do mapa colidirem.
_TEAM_ACCOUNT_BY_KEY = {
    key: TEAM_TO_SALESFORCE_ACCOUNT_MAPPING[canonical]
    for key, canonical in canonical_index(
        TEAM_TO_SALESFORCE_ACCOUNT_MAPPING, name='TEAM_TO_SALESFORCE_ACCOUNT_MAPPING'
    ).items()
}


def resolve_team_account_id(team: Optional[str]) -> Optional[str]:
    """Account Id do time, por `vocab_key`; `None` se o time não é destino mapeado.

    Fonte única da criação do Contact, da troca de time e da política de
    provedor. `Manhattan `, `MANHATTAN` e `manhattan` são o mesmo time; `SDR`
    (sinônimo de Prospecção) e erro de digitação continuam sem mapa.
    """
    return _TEAM_ACCOUNT_BY_KEY.get(vocab_key(team))


def dwteam_value_for_team(team: Optional[str]) -> Optional[str]:
    """Value of `User.DWTeam__c` for the register team (FBI-4842, decision D1).

    A partner team writes the flow TOKEN (Prospecção -> SDR, Mesa Digital
    Hunter -> Hunter), the same one Salesforce would derive from the Role.
    Before, MakersHub wrote the label after changing the Role and the label won
    over the flow. An internal team keeps the label. Empty -> None (no write).
    """
    label = (team or '').strip()
    if not label:
        return None
    account_id = resolve_team_account_id(label)
    if account_id and account_id in PARTNER_ACCOUNT_NAMES:
        return derive_dwteam_token(PARTNER_ACCOUNT_NAMES[account_id]) or label
    return label


def get_salesforce_connection(force_production: bool = False) -> Optional[Salesforce]:
    """
    Authenticate to Salesforce as the admin/service user via JWT Bearer flow.
    Used for read-only lookups (user resolution, lead queries, etc.).

    When force_production=True, always connects to production regardless of
    SF_IS_SANDBOX. Used by call sprint which reads leads from production DB
    and must write tasks back to production Salesforce.

    Requires SF_USERNAME, SF_JWT_CONSUMER_KEY, and SF_JWT_PRIVATE_KEY_FILE in .env.
    Returns Salesforce connection object or None if auth fails / not configured.
    """
    try:
        cache_key = "conn_prod" if force_production else "conn"
        cached_conn = _sf_connection_cache.get(cache_key)
        cached_expires = _sf_connection_cache.get(f"{cache_key}_expires", 0)
        if cached_conn and time.time() < cached_expires:
            return cached_conn

        # Double-checked locking: re-read cache after acquiring the lock.
        with _sf_admin_auth_lock:
            cached_conn = _sf_connection_cache.get(cache_key)
            cached_expires = _sf_connection_cache.get(f"{cache_key}_expires", 0)
            if cached_conn and time.time() < cached_expires:
                return cached_conn

            return _do_admin_jwt_auth(cache_key, force_production)

    except Exception as e:
        logger.error("Salesforce admin JWT auth failed: %s", e, exc_info=True)
        return None


def _do_admin_jwt_auth(cache_key: str, force_production: bool) -> Optional[Salesforce]:
    try:
        from app.core.config import GetSettings
        from pathlib import Path
        settings = GetSettings()

        sf_is_sandbox = False if force_production else settings.sfIsSandbox
        sf_username = settings.sfUsername if force_production else settings.sfEffectiveUsername
        consumer_key = settings.sfJwtConsumerKey if force_production else settings.sfEffectiveConsumerKey
        key_file = settings.sfJwtPrivateKeyFile

        if not all([sf_username, consumer_key, key_file]):
            message = (
                f"Missing Salesforce JWT credentials — "
                f"username={'SET' if sf_username else 'MISSING'}, "
                f"consumer_key={'SET' if consumer_key else 'MISSING'}, "
                f"key_file={'SET' if key_file else 'MISSING'}"
            )
            logger.error(message)
            return None

        # Resolve key file path (relative to backend dir)
        key_path = Path(key_file)
        if not key_path.is_absolute():
            backend_dir = Path(__file__).parent.parent.parent
            key_path = backend_dir / key_path

        if not key_path.exists():
            # Resiliência (2026-07-01): /dev/shm é tmpfs e o arquivo pode sumir
            # em runtime (observado 2× neste ambiente — integrações SF morriam
            # SILENCIOSAMENTE: POST 201, Contact nunca criado). Se o B64 está
            # no env (start.py o carrega), rematerializar aqui mesmo.
            b64 = os.getenv("SF_JWT_PRIVATE_KEY_B64", "").strip()
            if b64:
                try:
                    pem = base64.b64decode(b64)
                    if b"PRIVATE KEY" in pem:
                        key_path.parent.mkdir(parents=True, exist_ok=True)
                        key_path.write_bytes(pem)
                        os.chmod(key_path, 0o600)
                        logger.warning(
                            "JWT private key REMATERIALIZADA em %s (arquivo tmpfs havia sumido)",
                            key_path)
                except Exception as remat_error:
                    logger.error("Falha ao rematerializar JWT key: %s", remat_error)
            if not key_path.exists():
                logger.error("JWT private key not found: %s", key_path)
                return None

        domain = "test" if sf_is_sandbox else "login"
        logger.info(
            "Authenticating to Salesforce (JWT): user=%s, domain=%s, sandbox=%s",
            sf_username, domain, sf_is_sandbox,
        )

        sf = Salesforce(
            username=sf_username,
            consumer_key=consumer_key,
            privatekey_file=str(key_path),
            domain=domain,
            session=_sf_timeout_session(),
        )

        _sf_connection_cache[cache_key] = sf
        _sf_connection_cache[f"{cache_key}_expires"] = time.time() + SF_CONNECTION_TTL_SECONDS
        logger.info(
            "Successfully authenticated to Salesforce via JWT (%s) — instance: %s",
            "sandbox" if sf_is_sandbox else "production",
            sf.sf_instance,
        )
        return sf

    except Exception as e:
        logger.error("Failed to authenticate to Salesforce (JWT): %s", e)
        notify_teams_salesforce_error(str(e), operation="Salesforce JWT Authentication")
        return None


def is_jwt_flow_configured() -> bool:
    """Check whether the JWT Bearer flow settings are present."""
    from app.core.config import GetSettings
    settings = GetSettings()
    return bool(settings.sfJwtConsumerKey and settings.sfJwtPrivateKeyFile)


# ============================================================================
# ORG-SPECIFIC ID RESOLUTION
# ============================================================================
# All Salesforce IDs (User, Account, Profile, etc.) differ between production
# and sandbox.  These functions resolve critical IDs by name/email so that the
# only config change needed to switch environments is SF_IS_SANDBOX.

DANIEL_AMB_EMAIL = "daniel@ambfamilyoffice.com.br"
DANIEL_AMB_FULL_NAME = "Daniel Rodrigo Barbosa de Azevedo"
DANIEL_AMB_DISPLAY = "Daniel da AMB"


def get_admin_queue_owner_id(sf: Salesforce) -> Optional[str]:
    """
    Resolve the Salesforce User ID of the admin account that owns undistributed
    leads.  The JWT admin user (SF_USERNAME) is NOT necessarily the lead queue
    owner, so we auto-discover by sampling a recent undistributed lead.

    Priority:
    1. Cached value (avoids repeated queries)
    2. Explicit env var SF_LEAD_QUEUE_OWNER_ID (optional override)
    3. Auto-discover from a sample undistributed lead
    """
    cached = _resolved_org_ids.get("admin_owner_id")
    if cached:
        return cached

    explicit_id = os.getenv("SF_LEAD_QUEUE_OWNER_ID", "").strip()
    if explicit_id:
        _resolved_org_ids["admin_owner_id"] = explicit_id
        logger.info("Admin queue owner from SF_LEAD_QUEUE_OWNER_ID: %s", explicit_id)
        return explicit_id

    result = sf.query(
        "SELECT OwnerId, Owner.Name FROM Lead "
        "WHERE IsDeleted = false AND IsConverted = false "
        "AND Status IN ('Lead recebido', 'Esquentando') "
        "ORDER BY CreatedDate DESC LIMIT 1"
    )
    if result.get("totalSize", 0) > 0:
        owner_id = result["records"][0]["OwnerId"]
        owner_name = result["records"][0].get("Owner", {}).get("Name", "?")
        _resolved_org_ids["admin_owner_id"] = owner_id
        logger.info(
            "Auto-discovered lead queue owner: %s (%s)",
            owner_id, owner_name,
        )
        return owner_id

    logger.error(
        "Could not determine lead queue owner — no undistributed leads found "
        "and SF_LEAD_QUEUE_OWNER_ID is not set"
    )
    return None


def get_daniel_amb_user_id(sf: Salesforce) -> Optional[str]:
    """
    Resolve Daniel da AMB's Salesforce User ID for above-10M lead assignment.
    Queries by email (canonical) with name fallback.
    Cached for the connection lifetime.
    """
    cached = _resolved_org_ids.get("daniel_amb_id")
    if cached:
        return cached

    result = sf.query(
        f"SELECT Id, Name, Email FROM User "
        f"WHERE Email = '{DANIEL_AMB_EMAIL}' AND IsActive = true LIMIT 1"
    )
    if result.get("totalSize", 0) > 0:
        user_id = result["records"][0]["Id"]
        _resolved_org_ids["daniel_amb_id"] = user_id
        logger.info(
            "Resolved Daniel da AMB: %s (%s)",
            user_id, result["records"][0]["Name"],
        )
        return user_id

    result = sf.query(
        f"SELECT Id, Name FROM User "
        f"WHERE Name = '{DANIEL_AMB_FULL_NAME}' AND IsActive = true LIMIT 1"
    )
    if result.get("totalSize", 0) > 0:
        user_id = result["records"][0]["Id"]
        _resolved_org_ids["daniel_amb_id"] = user_id
        logger.info("Resolved Daniel da AMB (by name): %s", user_id)
        return user_id

    logger.error(
        "Could not resolve Daniel da AMB in Salesforce "
        "(email=%s) — above-10M assignment will fail",
        DANIEL_AMB_EMAIL,
    )
    return None


def resolve_sf_user_by_email(
    sf: Salesforce,
    email: str,
    fields: tuple = ("Id", "Name"),
    *,
    prefix_fallback: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Resolve the canonical active Salesforce User for a corporate email.

    An email can be shared by more than one active user. Two distinct shapes
    exist on this org (measured 2026-07-30: 11 duplicated @fazcapital.com.br
    emails):

    * **Re-created user** — when someone's User is rebuilt (licence swap,
      Standard -> PowerPartner, return from leave), Ops renames the old one
      ("- Inativo", "_prefix", ".old", ".invalid") and deactivates it, but does
      NOT change its Email. 7 of the 11 collisions are this.
    * **Service account** — a robot User reuses a person's email
      (``julio.balena@`` backs the person plus ``adminfc@`` and ``fazdigital@``,
      all three active).

    Neither "oldest" nor "newest" survives both shapes: oldest picks the dead
    user in every re-creation case, newest picks the robot in every service
    account case. What does survive is ``Username == Email`` — the canonical
    User keeps the plain corporate email as its username, while duplicates carry
    a suffix/prefix. That rule is right on 8/8 of the collisions that have any
    active user. CreatedDate DESC is only the tie-break for when no username
    matches (re-creation where both usernames were mangled), because there the
    live user is the newer one.

    This inverts the previous contract (CreatedDate ASC, "oldest wins"), which
    was written against sandbox-refresh test users and is refuted by production:
    it resolved e.g. renato.amaral@fazcapital.com.br to 005U5000007saldIAA
    ("- Inativo") instead of the live 005U500000Dq8lCIAR.

    A collision is itself a data smell, so whenever an email matches more than
    one active user we log it — resolution is a monitored fallback, and the
    duplicates should be merged in Salesforce.

    Note: we deliberately do NOT filter by UserType — real SDRs and specialists
    are portal (PowerPartner) users on this org, so a Standard-only filter would
    exclude them. When ``prefix_fallback`` is set, falls back to a
    username-prefix match (sandbox usernames sometimes carry a '.uat' suffix).

    Returns the matched record (with the requested ``fields``, plus ``Username``
    which the tie-break needs) or None.
    """
    if not sf or not email:
        return None
    target = email.strip().lower()
    # `fields` is developer-controlled (literal tuples at every call site); the
    # email is escaped (backslash first, then quote) before interpolation.
    # Username is appended when the caller did not ask for it: it is what breaks
    # the tie, and an extra key in the returned record is inert for callers.
    cols = ", ".join(fields if "Username" in fields else tuple(fields) + ("Username",))

    def _esc(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")

    def _esc_like(value: str) -> str:
        # A LIKE predicate treats '%' and '_' as wildcards on top of the
        # backslash/quote that _esc handles; escape all four (backslash first,
        # so the escapes we add are not themselves doubled) so the value matches
        # literally and an email local-part with '_' cannot widen the match.
        return (
            value.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
            .replace("'", "\\'")
        )

    def _pick(recs: List[Dict[str, Any]]) -> tuple[Dict[str, Any], str]:
        # Returns (record, rule) — the rule is what the warning below reports.
        # Saying "canonical username" on the fallback branch would strip Ops of
        # exactly the signal that tells the two collision shapes apart.
        for rec in recs:
            if str(rec.get("Username") or "").strip().lower() == target:
                return rec, "canonical username"
        return recs[0], "newest active (no canonical username)"

    def _first(predicate: str) -> Optional[Dict[str, Any]]:
        # LIMIT 5 (not 2): julio.balena@fazcapital.com.br has 3 active Users in
        # production, so LIMIT 2 could truncate the list before the canonical
        # username shows up. 5 covers the worst collision measured, with slack.
        #
        # `Id DESC` is not decoration: CreatedDate ties in production (two
        # platform Users created on the same second, neither carrying the
        # canonical username), and there `recs[0]` under CreatedDate alone is
        # undefined order — the fallback would lose the determinism that is the
        # whole point of this function. Same precedence as the airflow-dags
        # sibling (`toolkit/salesforce/user_sync.py`, PR #65), which already
        # breaks the tie by `(CreatedDate, Id)`.
        res = sf.query(
            f"SELECT {cols} FROM User "
            f"WHERE {predicate} AND IsActive = true "
            f"ORDER BY CreatedDate DESC, Id DESC LIMIT {_EMAIL_MATCH_LIMIT}"
        )
        recs = res.get("records") or []
        if not recs:
            return None
        picked, rule = _pick(recs)
        if len(recs) > 1:
            chosen = picked.get("attributes", {}).get("url", picked)
            logger.warning(
                "Salesforce email %r matches %d active users; resolving "
                "deterministically by %s (%s). "
                "Merge/de-duplicate these users in Salesforce.",
                email, len(recs), rule, chosen,
            )
        if len(recs) >= _EMAIL_MATCH_LIMIT:
            # Canary. The worst real collision is 3 active Users, so hitting the
            # cap means production went past what was measured — and a truncated
            # window can leave the canonical User outside it, silently demoting
            # the result to the fallback branch. Without this line the two paths
            # are indistinguishable in the logs.
            logger.error(
                "Salesforce email %r hit the %d-user query cap; the canonical "
                "User may have been truncated out of the window and the "
                "resolution may be wrong. Raise _EMAIL_MATCH_LIMIT and "
                "de-duplicate these users in Salesforce.",
                email, _EMAIL_MATCH_LIMIT,
            )
        return picked

    rec = _first(f"Email = '{_esc(email)}'")
    if rec is None and prefix_fallback:
        # Anchor on the FULL email, not just the local-part. The fallback exists
        # for sandbox usernames, which append a suffix to the whole email
        # (user@dom -> user@dom.sandbox), so 'email%' still matches them while
        # never matching a different person who merely shares a local-part prefix
        # (the old 'localpart%' matched 'daniel' -> daniel.guimaraes@..., a
        # different user). Wildcards in the value are escaped via _esc_like.
        rec = _first(f"Username LIKE '{_esc_like(email)}%'")
    return rec


def resolve_sf_user_id_by_email(sf: Salesforce, email: str) -> Optional[str]:
    """
    Resolve a Salesforce User ID by email address.
    Used for sandbox advisor ID resolution where production IDs from
    dim_advisor_scd2 don't exist.
    """
    rec = resolve_sf_user_by_email(sf, email, ("Id",), prefix_fallback=False)
    return rec["Id"] if rec else None


class UserLookupFailed(Exception):
    """The User query could not be executed (expired session, network, etc.)."""


def describe_users_by_ids(sf: Salesforce, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    ``{id: {"exists", "isActive", "name", "username"}}`` for each requested id.

    Keyed by the id the CALLER passed, so a config holding 15-char ids gets its
    own strings back. Malformed ids resolve to ``exists=False`` without reaching
    Salesforce — they can never identify a user.

    Raises UserLookupFailed when the query itself fails, so callers decide
    between failing open and surfacing "unknown" — the two want opposite things.
    """
    result: Dict[str, Dict[str, Any]] = {}
    valid: List[str] = []
    for uid in user_ids:
        if not uid:
            continue
        try:
            valid.append(_validate_sf_id(uid))
        except ValueError:
            logger.error("Salesforce routing id is malformed: %r", uid)
            result[uid] = {"exists": False, "isActive": False, "name": None, "username": None}

    if not valid:
        return result

    quoted = ", ".join(f"'{_esc_soql(uid)}'" for uid in valid)
    try:
        res = sf.query(
            f"SELECT Id, Name, Email, Username, IsActive FROM User WHERE Id IN ({quoted})"
        )
    except Exception as e:
        logger.error("User lookup failed for %s: %s", valid, e, exc_info=True)
        raise UserLookupFailed(str(e)) from e

    # SOQL accepts a 15-char id but always answers with the 18-char form, so the
    # match is on the case-sensitive 15-char prefix common to both.
    found = {(r.get("Id") or "")[:15]: r for r in res.get("records") or []}
    for uid in valid:
        rec = found.get(uid[:15])
        result[uid] = {
            "exists": rec is not None,
            "isActive": bool(rec.get("IsActive")) if rec else False,
            "name": rec.get("Name") if rec else None,
            "email": rec.get("Email") if rec else None,
            "username": rec.get("Username") if rec else None,
        }
    return result


def filter_active_user_ids(sf: Salesforce, user_ids: List[str]) -> set[str]:
    """
    Subset of ``user_ids`` whose Salesforce User is active.

    Salesforce refuses any DML that would leave an inactive user as the owner of
    a record (``INACTIVE_OWNER_OR_USER``), so a routing target has to be checked
    BEFORE the first write: once the Lead has converted there is no way to fail
    cleanly anymore.

    Fail-open on query error (returns every id), mirroring verify_slot: losing
    the check must not block a booking whose target is perfectly fine.
    """
    ids = [uid for uid in user_ids if uid]
    if not ids:
        return set()
    try:
        described = describe_users_by_ids(sf, ids)
    except UserLookupFailed:
        return set(ids)
    return {uid for uid, info in described.items() if info.get("isActive")}


def user_has_api_access(sf_admin: Optional[Salesforce], user_email: Optional[str]) -> bool:
    """
    Whether the Salesforce User for ``user_email`` can make REST API calls.

    True iff their Profile has "API Enabled" OR any assigned permission set grants
    it. Resolved via the admin connection and cached per email (same TTL as the
    connections) because a portal user without API access can still obtain a JWT
    session — only the data call fails — so the per-user connection looks usable
    but isn't. Unknown user resolves to False (caller routes the write to admin,
    which still succeeds).
    """
    if not sf_admin or not user_email:
        return False

    cached = _user_api_access_cache.get(user_email)
    if cached and time.time() < cached.get("expires", 0):
        return bool(cached["value"])

    value = _query_user_api_access(sf_admin, user_email)
    _user_api_access_cache[user_email] = {
        "value": value,
        "expires": time.time() + SF_CONNECTION_TTL_SECONDS,
    }
    return value


def _query_user_api_access(sf_admin: Salesforce, user_email: str) -> bool:
    try:
        rec = resolve_sf_user_by_email(
            sf_admin, user_email, ("Id", "Profile.PermissionsApiEnabled")
        )
        if not rec:
            logger.warning(
                "user_has_api_access: no SF user for %s — treating as no API access",
                user_email,
            )
            return False

        profile = rec.get("Profile") or {}
        if profile.get("PermissionsApiEnabled"):
            return True

        user_id = _validate_sf_id(rec["Id"])
        res = sf_admin.query(
            f"SELECT count() FROM PermissionSetAssignment "
            f"WHERE AssigneeId = '{user_id}' "
            f"AND PermissionSet.PermissionsApiEnabled = true"
        )
        return (res.get("totalSize") or 0) > 0
    except Exception as e:
        # On a lookup error, fail safe to "no API access": the write falls back to
        # the admin connection (conversion still completes) rather than risking an
        # API_CURRENTLY_DISABLED that fails the whole flow.
        logger.warning("user_has_api_access lookup failed for %s: %s", user_email, e)
        return False


def resolve_write_connection(
    sf_admin: Salesforce,
    sf_user_connection: Optional[Salesforce],
    user_email: Optional[str],
) -> Salesforce:
    """
    Pick the connection to WRITE with in the R1 flows.

    Prefer the per-user connection (so "Created By" = the real operator), but fall
    back to the admin connection when there is no per-user connection OR the
    operator's SF profile can't make API calls — otherwise the per-user write dies
    with API_CURRENTLY_DISABLED and the lead is silently never converted.
    """
    if not sf_user_connection:
        return sf_admin
    if not user_email:
        logger.warning(
            "R1 write routed through admin: no operator email to verify API access."
        )
        return sf_admin
    if not user_has_api_access(sf_admin, user_email):
        logger.warning(
            "R1 write routed through admin: SF user %s lacks API access "
            "(Profile/PermissionSet PermissionsApiEnabled=false). Conversion will "
            "complete as admin; Created By will be the integration user.",
            user_email,
        )
        return sf_admin
    return sf_user_connection


def resolve_salesforce_username(sf_admin: Salesforce, user_email: str) -> Optional[str]:
    """
    Look up a Salesforce User's Username by their corporate email.
    Returns the exact Username string needed for JWT auth, or None.
    """
    rec = resolve_sf_user_by_email(sf_admin, user_email, ("Username",))
    if rec:
        logger.info("resolve_salesforce_username: %s → %s", user_email, rec["Username"])
        return rec["Username"]
    logger.warning("resolve_salesforce_username: no SF User found for %s", user_email)
    return None


def get_salesforce_connection_as_user(user_email: str, force_production: bool = False) -> Optional[Salesforce]:
    """
    Authenticate to Salesforce **as a specific user** via OAuth 2.0 JWT Bearer Token Flow.

    This makes the "Created By" field show the real user instead of the API admin account.

    When force_production=True, always connects to production regardless of
    SF_IS_SANDBOX. Used by call sprint.

    Requirements (one-time Salesforce admin setup):
    - A Connected App with a digital certificate (see docs/salesforce_jwt_setup.md)
    - SF_JWT_CONSUMER_KEY and SF_JWT_PRIVATE_KEY_FILE set in .env
    - Each target user pre-authorized in the Connected App

    Falls back to None if JWT isn't configured or the user has no Salesforce account.
    """
    if not is_jwt_flow_configured():
        logger.debug("JWT flow not configured — SF_JWT_CONSUMER_KEY or SF_JWT_PRIVATE_KEY_FILE empty")
        return None

    # Check cache (separate cache key for forced production)
    cache_key = f"{user_email}:prod" if force_production else user_email
    cached = _sf_user_connection_cache.get(cache_key)
    if cached and time.time() < cached.get("expires", 0):
        return cached["conn"]

    user_lock = _get_user_auth_lock(cache_key)
    with user_lock:
        cached = _sf_user_connection_cache.get(cache_key)
        if cached and time.time() < cached.get("expires", 0):
            return cached["conn"]

        return _do_user_jwt_auth(user_email, cache_key, force_production)


def _do_user_jwt_auth(user_email: str, cache_key: str, force_production: bool) -> Optional[Salesforce]:
    from app.core.config import GetSettings
    from pathlib import Path
    settings = GetSettings()

    try:
        # Step 1: Use admin connection to resolve the exact Salesforce Username
        sf_admin = get_salesforce_connection(force_production=force_production)
        if not sf_admin:
            logger.error("JWT flow: cannot resolve username — admin connection failed")
            return None

        sf_username = resolve_salesforce_username(sf_admin, user_email)
        if not sf_username:
            logger.warning(
                "JWT flow: user %s has no Salesforce account. "
                "Cannot authenticate as this user.",
                user_email,
            )
            return None

        # Step 2: Resolve the private key file path (relative to backend/ dir)
        key_path = Path(settings.sfJwtPrivateKeyFile)
        if not key_path.is_absolute():
            # Relative to the backend directory (where .env lives)
            backend_dir = Path(__file__).parent.parent.parent
            key_path = backend_dir / key_path

        if not key_path.exists():
            logger.error("JWT flow: private key file not found at %s", key_path)
            return None

        # Step 3: Authenticate via JWT Bearer flow
        sf_is_sandbox = False if force_production else settings.sfIsSandbox
        consumer_key = settings.sfJwtConsumerKey if force_production else settings.sfEffectiveConsumerKey
        domain = "test" if sf_is_sandbox else "login"
        logger.info(
            "JWT flow: authenticating as %s (domain=%s, consumer_key=%s...)",
            sf_username, domain, consumer_key[:10],
        )

        sf_user = Salesforce(
            username=sf_username,
            consumer_key=consumer_key,
            privatekey_file=str(key_path),
            domain=domain,
            session=_sf_timeout_session(),
        )

        # Cache with same TTL as admin connection
        _sf_user_connection_cache[cache_key] = {
            "conn": sf_user,
            "expires": time.time() + SF_CONNECTION_TTL_SECONDS,
        }
        logger.info(
            "JWT flow: authenticated as %s — instance: %s (Created By will show this user)",
            sf_username, sf_user.sf_instance,
        )
        return sf_user

    except Exception as e:
        error_msg = str(e)
        # Distinguish "user not pre-authorized" from other errors
        if "invalid_grant" in error_msg.lower() or "user hasn't approved" in error_msg.lower():
            logger.warning(
                "JWT flow: user %s exists but is NOT pre-authorized in the Connected App. "
                "Ask a Salesforce admin to authorize them. Error: %s",
                user_email, error_msg,
            )
        else:
            logger.error("JWT flow: failed to authenticate as %s: %s", user_email, e, exc_info=True)
        return None


def get_profile_ids(sf: Salesforce) -> bool:
    """
    Fetch Salesforce Profile IDs for Partner Users.
    Returns True if both profiles were found successfully.
    """
    global PROFILE_ASSESSOR_ID, PROFILE_SDR_ID

    try:
        query = "SELECT Id FROM Profile WHERE Name = 'Portal - Assessor'"
        result = sf.query(query)
        if result.get('totalSize', 0) > 0:
            PROFILE_ASSESSOR_ID = result['records'][0]['Id']
            logger.info("Profile 'Portal - Assessor' found: %s",
                        PROFILE_ASSESSOR_ID)
        else:
            logger.error("Profile 'Portal - Assessor' not found in Salesforce")

        query = "SELECT Id FROM Profile WHERE Name = 'Portal - SDR'"
        result = sf.query(query)
        if result.get('totalSize', 0) > 0:
            PROFILE_SDR_ID = result['records'][0]['Id']
            logger.info("Profile 'Portal - SDR' found: %s", PROFILE_SDR_ID)
        else:
            logger.error("Profile 'Portal - SDR' not found in Salesforce")

        return PROFILE_ASSESSOR_ID is not None and PROFILE_SDR_ID is not None

    except Exception as e:
        logger.error("Error fetching profile IDs: %s", e)
        return False


def generate_random_password(length: int = 10) -> str:
    """
    Generate a random password with letters, numbers, and special characters.
    """
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(chars) for _ in range(length))

    if not any(c.isupper() for c in password):
        password = password[:1] + random.choice(
            string.ascii_uppercase) + password[2:]
    if not any(c.islower() for c in password):
        password = password[:2] + random.choice(
            string.ascii_lowercase) + password[3:]
    if not any(c.isdigit() for c in password):
        password = password[:3] + random.choice(string.digits) + password[4:]
    if not any(c in "!@#$%^&*" for c in password):
        password = password[:4] + random.choice("!@#$%^&*") + password[5:]

    return password


def enable_partner_user(sf: Salesforce,
                        contact_id: str,
                        email: str,
                        name: str,
                        area: Optional[str] = None,
                        team: Optional[str] = None,
                        profile_id: Optional[str] = None,
                        is_leader: bool = False,
                        info: Optional[Dict[str, Any]] = None,
                        position: Optional[str] = None,
                        salesforce_access_role: Optional[str] = None,
                        ignore_user_ids: Optional[Any] = None) -> Optional[str]:
    """
    Enable a Partner User for the contact based on area and team criteria.

    Args:
        sf: Salesforce connection
        contact_id: Salesforce Contact ID
        email: Email for the user
        name: Full name of the user
        area: Area of the employee (optional)
        team: Team of the employee (optional)
        position: Função canônica do colaborador na taxonomia FBI-2956
        profile_id: Explicit Profile ID to use (optional, overrides area/team logic)
        is_leader: líder de time de assessoria/mesa → Portal - Head (Fase 1)
        info: dict OUT opcional — recebe error_code/needs_manual_reactivation
              para o chamador distinguir licença esgotada de timeout etc.
    """
    if not email:
        logger.warning(
            "Cannot enable Partner User for contact %s: No email provided",
            contact_id)
        return None

    # Fase 1 (2026-07-01): resolução ÚNICA de profile — nome via tabela empírica
    # (eligibility.resolve_salesforce_profile_name) + Id resolvido por Name no
    # SF live. Substitui o resolvedor inline que só conhecia Assessor/SDR e
    # deixava Seguros/Consórcio/XP Int. em partial_success eterno (gap A1).
    if not profile_id:
        profile_name = resolve_salesforce_profile_name(
            area,
            team,
            is_leader,
            position=position,
            salesforce_access_role=salesforce_access_role,
        )
        if profile_name:
            profile_id = get_profile_id_by_name(sf, profile_name)

    if not profile_id:
        logger.warning("No profile ID for area=%s, team=%s, is_leader=%s", area, team, is_leader)
        if info is not None:
            info['error_code'] = 'NO_PROFILE_FOR_CRITERIA'
        return None

    try:
        # NOTA: a busca por ContactId é sabidamente NÃO confiável neste org p/
        # o usuário de API (FLS/sharing) — por isso há fallback por Username
        # adiante (achado da sessão de QA 2026-07-01).
        query = f"SELECT Id, IsActive FROM User WHERE ContactId = '{_validate_sf_id(contact_id)}'"
        result = sf.query(query)

        if result.get('totalSize', 0) > 0:
            user_id = result['records'][0]['Id']
            is_active = result['records'][0].get('IsActive', False)

            if is_active:
                logger.info("Partner User already exists and is active: %s",
                            user_id)
                return user_id
            # Recontratação (Fase 2.3): reativar pelo caminho CORRETO —
            # IsActive + IsPortalEnabled juntos (enable_partner_user_via_api).
            # O update IsActive isolado é bloqueado pelo SF p/ Portal Users.
            logger.info(
                "Partner User exists but is inactive: %s. Reactivating via API...",
                user_id)
            reactivation = enable_partner_user_via_api(sf, user_id)
            if reactivation.get('success'):
                return user_id
            logger.error("❌ Reativação via API falhou: %s", reactivation.get('message'))
            if info is not None:
                info['needs_manual_reactivation'] = True
                info['inactive_user_id'] = user_id
            return None

        # Username e FederationIdentifier devem usar o corporate_email diretamente
        username = email  # corporate_email como Username
        alias = name.replace(' ', '').lower()[:8]

        # O(s) Id(s) que o chamador já decidiu substituir não contam como
        # colisão — ver a docstring de `resolve_salesforce_identities`. Na
        # conversão Standard -> Partner o Email da conta de origem continua o
        # mesmo, e sem esta exclusão o DUPLICATE_EMAIL abaixo recusaria a
        # criação apontando para a própria conta que está sendo substituída.
        ignorados = {
            str(uid).strip()
            for uid in (
                [ignore_user_ids] if isinstance(ignore_user_ids, str)
                else (ignore_user_ids or [])
            )
            if str(uid).strip()
        }

        def _sem_ignorados(registros):
            return [
                r for r in (registros or [])
                if str(r.get('Id', '')).strip() not in ignorados
            ]

        # Username já existe? Pode ser RECONTRATAÇÃO cujo lookup por ContactId
        # falhou (ver nota acima) — inspecionar o dono antes de desistir.
        username_query = f"SELECT Id, IsActive, ContactId FROM User WHERE Username = '{_esc_soql(username)}'"
        username_result = sf.query(username_query)
        username_records = _sem_ignorados(username_result.get('records'))

        if username_records:
            existing = username_records[0]
            existing_id = existing['Id']
            if not existing.get('IsActive', False):
                logger.info(
                    "Username '%s' pertence a User INATIVO (%s) — reativando via API (recontratação)",
                    username, existing_id)
                reactivation = enable_partner_user_via_api(sf, existing_id)
                if reactivation.get('success'):
                    return existing_id
                if info is not None:
                    info['needs_manual_reactivation'] = True
                    info['inactive_user_id'] = existing_id
                return None
            logger.error(
                "❌ Username '%s' já existe ATIVO no Salesforce (User %s, Contact %s ≠ %s).",
                username, existing_id, existing.get('ContactId'), contact_id)
            if info is not None:
                info['error_code'] = 'DUPLICATE_USERNAME'
            return None

        email_query = f"SELECT Id FROM User WHERE Email = '{_esc_soql(email)}'"
        email_result = sf.query(email_query)

        if _sem_ignorados(email_result.get('records')):
            logger.error("Email '%s' already belongs to a Salesforce User; refusing duplicate creation", email)
            if info is not None:
                info['error_code'] = 'DUPLICATE_EMAIL'
            return None

        user_data = {
            'Username': username,
            'Email': email,
            'LastName': name.split(' ')[-1] if ' ' in name else name,
            'FirstName': ' '.join(name.split(' ')[:-1]) if ' ' in name else '',
            'Alias': alias,
            'TimeZoneSidKey': 'America/Sao_Paulo',
            'LocaleSidKey': 'pt_BR',
            'EmailEncodingKey': 'UTF-8',
            'LanguageLocaleKey': 'pt_BR',
            'ContactId': contact_id,
            'ProfileId': profile_id,
            'IsActive': True,
            'FederationIdentifier':
            username  # FederationIdentifier igual ao Username (corporate_email)
        }

        try:
            result = sf.User.create(user_data)  # type: ignore
            if result.get('success'):
                user_id = result.get('id')
                logger.info("Partner User created successfully: %s", user_id)
                return user_id
            else:
                logger.error("Failed to create Partner User: %s", result)
                return None
        except Exception as create_error:
            # Fase 1.3: erro TIPADO — licença esgotada (163/168 usadas!) tem que
            # ser distinguível de timeout/perfil inválido no resultado.
            error_code = _extract_sf_error_code(create_error)
            logger.error("Error creating Partner User (errorCode=%s): %s",
                         error_code, create_error)
            if info is not None and error_code:
                info['error_code'] = error_code
            if error_code == 'LICENSE_LIMIT_EXCEEDED':
                notify_teams_salesforce_error(
                    f"LICENÇA PARTNER COMMUNITY ESGOTADA ao criar user p/ {name} — "
                    "liberar licenças presas ou comprar mais.",
                    employee_name=name,
                    operation="Criar Partner User",
                )
            return None

    except Exception as e:
        logger.error("Error enabling Partner User for Contact %s: %s",
                     contact_id, e)
        return None


# (update_salesforce_ids_in_db removida na Fase 3.7, 2026-07-01: dead code —
#  zero chamadores; os writers reais gravam inline no repository, só em sensitive.
#  O espelho public.dim_employee_scd2 é responsabilidade dos triggers de sync.)


def sync_salesforce_create_contact_and_enable_partner(
        employee_data: Dict[str, Any],
        session: Optional[AsyncSession] = None,
        ignore_user_ids: Optional[Any] = None) -> Dict[str, Any]:
    """
    Create a Contact in Salesforce, return ID, update database, and enable Partner User.
    Who reaches here is decided by `eligibility.should_have_partner_user`.

    NOTE: This is a SYNCHRONOUS function that runs in executor.
    """
    try:
        employee_id = employee_data.get('employee_sk')
        name = employee_data.get('name')
        first_name = employee_data.get('first_name')
        last_name = employee_data.get('last_name')
        email = (employee_data.get('email')
                 or employee_data.get('corporate_email')
                 or employee_data.get('personal_email'))
        area = employee_data.get('area')
        team = employee_data.get('team')
        position = employee_data.get('position')
        salesforce_access_role = employee_data.get('salesforce_access_role')

        if not employee_id:
            return {
                'success': False,
                'message': 'ID do colaborador (employee_sk) é obrigatório'
            }

        if not name or not first_name or not last_name:
            return {'success': False, 'message': 'Nome completo é obrigatório'}

        if not email:
            return {'success': False, 'message': 'Email é obrigatório'}

        if not should_have_partner_user(
            area,
            team,
            position,
            salesforce_access_role=salesforce_access_role,
        ):
            return {
                'success':
                False,
                'message':
                f'Colaborador não atende aos critérios (area={area}, team={team})'
            }

        sf = get_salesforce_connection()
        if not sf:
            notify_teams_salesforce_error(
                "Falha na autenticacao com o Salesforce",
                employee_name=name,
                operation="Criar Contact/Partner User",
            )
            return {
                'success': False,
                'message': 'Falha na autenticação com o Salesforce'
            }

        if not get_profile_ids(sf):
            return {
                'success': False,
                'message': 'Falha ao obter Profile IDs do Salesforce'
            }

        contact_id = employee_data.get('salesforce_contact_id')
        identity = resolve_salesforce_identities(
            sf, contact_id, str(email), ignore_user_ids=ignore_user_ids
        )
        identity_status = identity['status']
        if identity_status == 'active_partner':
            user = identity['record']
            canonical_contact_id = user.get('ContactId') or contact_id
            if not canonical_contact_id:
                return {
                    'success': False,
                    'message': 'Partner User existente sem ContactId; revisão manual necessária',
                    'error_code': 'IDENTITY_CONTACT_MISSING',
                }
            return {
                'success': True,
                'message': 'Partner User existente localizado sem criar nova identidade',
                'contact_id': canonical_contact_id,
                'salesforce_user_id': user['Id'],
                'identity_reused': True,
            }
        if identity_status != 'none':
            return {
                'success': False,
                'message': 'Identidade Salesforce existente requer revisão manual; nenhuma escrita foi executada',
                'error_code': f"IDENTITY_{identity_status.upper()}",
                'manual_required': True,
            }

        if contact_id:
            contact_id = _validate_sf_id(str(contact_id))
            result = sf.query(
                f"SELECT Id FROM Contact WHERE Id = '{contact_id}' LIMIT 1"
            )
            if not (result.get('records') or []):
                return {
                    'success': False,
                    'message': f'Contact canônico {contact_id} não encontrado',
                    'error_code': 'CANONICAL_CONTACT_NOT_FOUND',
                }
        else:
            query = f"SELECT Id FROM Contact WHERE Email = '{_esc_soql(email)}'"
            result = sf.query(query)
            if result.get('totalSize', 0) > 0:
                contact_id = result['records'][0]['Id']
                logger.info("Contact already exists by email fallback: %s", contact_id)

        if not contact_id:
            if not team:
                return {
                    'success': False,
                    'message': 'TIME é obrigatório para criar Partner User'
                }

            # Determinar AccountId baseado no team
            account_id = resolve_team_account_id(team)
            if account_id is not None:
                logger.info("Using mapped Account for team '%s': %s", team,
                            account_id)
            else:
                # Fase 1 (2026-07-01): ABORT explícito — o fallback antigo
                # (FAZ_CAPITAL_ACCOUNT_ID) é um Id INEXISTENTE na org de
                # produção (0 hits em 44.891 accounts do espelho staging) e
                # ancorava o Contact num registro fantasma. O legado Streamlit
                # também abortava aqui.
                error_msg = (
                    f"Team '{team}' sem Account mapeada em "
                    "TEAM_TO_SALESFORCE_ACCOUNT_MAPPING — cadastre o mapeamento "
                    "antes de criar o Contact (abort explícito, sem fallback)."
                )
                logger.error(error_msg)
                notify_teams_salesforce_error(
                    error_msg, employee_name=name, operation="Criar Contact")
                return {'success': False, 'message': error_msg,
                        'error_code': 'TEAM_ACCOUNT_UNMAPPED'}

            contact_data = {
                'FirstName':
                first_name,
                'LastName':
                last_name,
                'Email':
                email,
                'Phone':
                employee_data.get('phone'),
                'MobilePhone':
                employee_data.get('mobile_phone'),
                'Title':
                employee_data.get('position'),
                'Birthdate': (birth_date.isoformat() if
                              (birth_date := employee_data.get('birth_date'))
                              and isinstance(birth_date, date) else None),
                'DWCodigoAssessorXP__c':
                employee_data.get('advisor_code'),
                'MailingCity':
                employee_data.get('city'),
                'MailingState':
                employee_data.get('state'),
                'MailingStreet':
                employee_data.get('address'),
                'MailingPostalCode':
                employee_data.get('zip_code'),
                'Department':
                employee_data.get('sector'),
                'AccountId':
                account_id  # OBRIGATÓRIO para Partner Users
            }

            contact_data = {
                k: v
                for k, v in contact_data.items() if v is not None
            }

            result = sf.Contact.create(contact_data)  # type: ignore

            if not result.get('success'):
                error_msg = f"Falha ao criar Contact: {result}"
                logger.error(error_msg)
                notify_teams_salesforce_error(
                    error_msg,
                    employee_name=name,
                    operation="Criar Contact",
                )
                return {'success': False, 'message': error_msg}

            contact_id = result.get('id')
            logger.info("Contact created: %s", contact_id)

        partner_info: Dict[str, Any] = {}
        user_id = enable_partner_user(
            sf, contact_id, email, name, area, team,
            is_leader=bool(employee_data.get('is_leader')),
            info=partner_info,
            position=position,
            salesforce_access_role=employee_data.get('salesforce_access_role'),
            ignore_user_ids=ignore_user_ids,
        )

        if user_id:
            # Database update is handled by the caller (employee_repository)
            # since this function runs in executor and can't await

            success_message = f"Contact criado (ID: {contact_id}) e Partner User habilitado (User ID: {user_id})"
            return {
                'success': True,
                'message': success_message,
                'contact_id': contact_id,
                'salesforce_user_id': user_id
            }
        else:
            # Fase 1.3: propagar o motivo TIPADO (licença esgotada, username
            # duplicado, reativação manual pendente...) em vez de mensagem cega.
            error_code = partner_info.get('error_code')
            detail = f" [{error_code}]" if error_code else ""
            if partner_info.get('needs_manual_reactivation'):
                detail += (
                    f" — User inativo {partner_info.get('inactive_user_id')} exige "
                    "reativação MANUAL no Salesforce (Contact > Enable Partner User)"
                )
            warning_message = (
                f"Contact criado (ID: {contact_id}), mas falha ao habilitar Partner User{detail}"
            )
            logger.warning(warning_message)
            return {
                'success': False,
                'message': warning_message,
                'contact_id': contact_id,
                'partial_success': True,
                'error_code': error_code,
                'needs_manual_reactivation': partner_info.get('needs_manual_reactivation', False),
            }

    except Exception as e:
        error_msg = f"Erro ao criar Contact e habilitar Partner User: {str(e)}"
        logger.error(error_msg)
        notify_teams_salesforce_error(
            error_msg,
            employee_name=employee_data.get("name"),
            operation="Criar Contact/Partner User",
        )
        return {'success': False, 'message': error_msg}


def reconcile_salesforce_access_role(
    existing_user_id: str,
    employee_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Reconcile an explicit role without deriving access from HR taxonomy.

    A ProfileId update is sufficient only inside the PowerPartner licence.
    Standard -> PowerPartner needs a new portal User. The old username is
    parked first, the Partner User is created, and only then is the Standard
    User deactivated. If creation fails, the original username is restored.
    """
    sf = get_salesforce_connection()
    if not sf:
        return {'success': False, 'message': 'Falha na autenticação com o Salesforce'}

    user_id = _validate_sf_id(existing_user_id)
    current_result = sf.query(
        "SELECT Id, ContactId, IsActive, UserType, Username, Email, "
        f"FederationIdentifier, Profile.Name FROM User WHERE Id = '{user_id}' LIMIT 1"
    )
    records = current_result.get('records') or []
    if not records:
        return {'success': False, 'message': f'Usuário {user_id} não encontrado'}

    current = records[0]
    if current.get('UserType') == 'PowerPartner':
        result = update_user_profile_for_area_change(user_id, employee_data)
        result['salesforce_user_id'] = user_id
        # The employee row may predate the ContactId reconciliation.  Returning
        # the ContactId lets the repository repair only its local reference;
        # this path does not create or update a Salesforce Contact/User.
        result['contact_id'] = current.get('ContactId')

        # O Perfil sozinho não muda o time: o Account do Contact e o Papel
        # (UserRole) carregam a hierarquia do time. Reconcilia os dois no mesmo
        # passo — só quando o Perfil pôde ser reconciliado, porque papel vazio
        # ou inelegível significa "não mexer no Salesforce" (FBI-4842).
        #
        # A ORDEM importa: o Account do Contact vem PRIMEIRO. O UserRole de um
        # Partner User precisa ser compatível com o Account do Contact; atribuir
        # o Papel do time novo com o Contact ainda no Account antigo faz o
        # Salesforce recusar com FIELD_INTEGRITY_EXCEPTION ("Invalid role
        # assignment") — reproduzido ao vivo em 2026-10-06.
        if result.get('success'):
            contact_id = current.get('ContactId')
            team = employee_data.get('team')
            if contact_id and team:
                account_result = update_contact_account(
                    str(contact_id), str(team), str(employee_data.get('name') or '')
                )
                result['contact_account'] = account_result
                if not account_result.get('success'):
                    result['success'] = False
                    result['partial_success'] = True
                if account_result.get('message'):
                    result['message'] = _join_messages(
                        result.get('message'), account_result['message']
                    )

            role_result = update_salesforce_user_role(user_id, employee_data)
            result['user_role'] = role_result
            if not role_result.get('success'):
                result['success'] = False
                result['partial_success'] = True
            if role_result.get('message'):
                result['message'] = _join_messages(
                    result.get('message'), role_result['message']
                )
        return result
    if current.get('UserType') != 'Standard':
        return {
            'success': False,
            'message': (
                f"Conversão automática recusada para UserType "
                f"{current.get('UserType')!r}"
            ),
        }

    # GUARD DO T1 (decisão D[6], 2026-09-04) — elegibilidade DERIVADA nunca
    # converte User que já existe. Só papel partner_* escolhido por um humano
    # troca licença interna (Standard) por licença de portal (PowerPartner).
    #
    # Sem este guard, a derivação do T1 tornaria 4 gestores elegíveis e a
    # próxima edição de área/time/função/is_leader deles estacionaria o
    # Username, criaria um Partner User e DESATIVARIA o Standard — perda de
    # acesso interno que ninguém pediu. Medido em 2026-09-08, os 4 são:
    # 96 Everton (Head do Advisory, profile "TI"), 188 Jullya (Head Assessoria,
    # "Heads"), 1473 Talise (Head de Assessoria de Prospecção, "TI") e
    # 125 Cristiano (Líder de Prospecção, "TI").
    #
    # Hoje isso não acontece só porque a conversão morre antes, por falta de
    # profile; com o profile derivado (D[5]) ela passaria a funcionar. Por isso
    # guard e derivação entram no MESMO commit.
    if not role_is_explicit_partner(employee_data.get('salesforce_access_role')):
        return {
            'success': False,
            'message': (
                'User Standard preservado: elegibilidade derivada não converte '
                'licença interna em licença de portal. Preencha '
                'salesforce_access_role para converter deliberadamente.'
            ),
            'salesforce_user_id': user_id,
            'standard_user_preserved': True,
        }

    original_username = current.get('Username')
    original_federation = current.get('FederationIdentifier')
    original_email = current.get('Email')
    if not original_username:
        return {'success': False, 'message': 'Standard User sem Username'}

    # O EMAIL É ESTACIONADO JUNTO, e não é detalhe cosmético.
    #
    # No Salesforce o Username é único no mundo, mas o Email NÃO é. Estacionar
    # só o Username deixava a conta aposentada com o mesmo Email da conta nova,
    # e a partir daí `resolve_salesforce_identities` achava as duas por Email e
    # devolvia `ambiguous` — congelando a pessoa para sincronização e
    # recontratação, permanentemente, depois de uma conversão bem-sucedida.
    # Reproduzido em 2026-09-10; ver `test_standard_to_partner_conversion.py`.
    #
    # Perder o endereço real na conta aposentada não custa nada: ela já vai
    # inativa e com o Username mutilado. O que ela não pode é continuar
    # disputando identidade com a conta viva.
    stamp = int(time.time())
    parked_username = f"{original_username}{STANDARD_MIGRATED_MARKER}{stamp}"
    parked_federation = f"standard-migrated-{user_id}-{stamp}"
    parked_fields: Dict[str, Any] = {
        'Username': parked_username,
        'FederationIdentifier': parked_federation,
    }
    if original_email:
        parked_fields['Email'] = _park_email(str(original_email), stamp)
    # Restaurar tem que devolver os MESMOS campos que o estacionamento mexeu —
    # senão a conta volta meio estacionada e ninguém percebe.
    restore_fields: Dict[str, Any] = {
        'Username': original_username,
        'FederationIdentifier': original_federation,
    }
    if original_email:
        restore_fields['Email'] = original_email

    sf.User.update(user_id, parked_fields)  # type: ignore

    new_user_id = None
    try:
        create_payload = dict(employee_data)
        full_name = str(create_payload.get('name') or '').strip()
        name_parts = full_name.split()
        create_payload.setdefault('first_name', name_parts[0] if name_parts else '')
        create_payload.setdefault(
            'last_name',
            ' '.join(name_parts[1:]) if len(name_parts) > 1 else full_name,
        )
        create_payload.setdefault(
            'email',
            create_payload.get('corporate_email')
            or create_payload.get('personal_email'),
        )
        # O Standard que estamos convertendo continua existindo entre o
        # estacionamento e a criação. O trio estacionado (Username,
        # FederationIdentifier E Email, desde 354b49071) já não casa com
        # nada — mas o Id segue o mesmo, e é PELO Id que `ignore_user_ids`
        # filtra (Id não é predicado do resolvedor: os predicados são
        # ContactId, Username, Email e FederationIdentifier). Sem ignorá-lo,
        # SE o cadastro carrega `salesforce_contact_id` E a conta de origem
        # o carrega, a resolução reencontra esta conta pelo ContactId e a
        # conversão se auto-recusa com `standard_or_other`, restaurando os
        # campos. A auto-recusa pelo Email é o mecanismo ORIGINAL,
        # reproduzido na manhã de 2026-09-10, antes do Email ser estacionado
        # (354b49071, 13:44) — ver `test_standard_to_partner_conversion.py`.
        created = sync_salesforce_create_contact_and_enable_partner(
            create_payload, ignore_user_ids=[user_id]
        )
        new_user_id = created.get('salesforce_user_id')
        if not created.get('success') or not new_user_id:
            sf.User.update(user_id, restore_fields)  # type: ignore
            return created

        sf.User.update(user_id, {'IsActive': False})  # type: ignore
        return {
            'success': True,
            'message': (
                'Standard User preservado como inativo e novo Partner User '
                'habilitado com o entitlement explícito'
            ),
            'salesforce_user_id': new_user_id,
            'contact_id': created.get('contact_id'),
            'replaced_salesforce_id': user_id,
        }
    except Exception:
        # Once the Partner User owns the canonical username, restoring it on
        # the still-active Standard User would create a second failure (or a
        # duplicate identity). At that point the safe recoverable state is:
        # Partner created, Standard parked, deactivation pending retry/manual
        # intervention. The caller receives both ids to reconcile explicitly.
        if new_user_id:
            logger.exception(
                'Partner User criado, mas Standard User nao foi desativado: %s',
                user_id,
            )
            return {
                'success': False,
                'partial_success': True,
                'message': (
                    'Partner User criado, mas o Standard User anterior nao '
                    'foi desativado; identidade original permaneceu estacionada'
                ),
                'salesforce_user_id': new_user_id,
                'contact_id': created.get('contact_id'),
                'replaced_salesforce_id': user_id,
                'needs_manual_standard_deactivation': True,
            }
        try:
            sf.User.update(user_id, restore_fields)  # type: ignore
        except Exception:
            logger.exception(
                'Falha ao restaurar Standard User após conversão interrompida: %s',
                user_id,
            )
        raise


def enable_partner_user_via_api(sf: Salesforce,
                                user_id: str) -> Dict[str, Any]:
    """
    ENABLE/REACTIVATE a Partner User by setting IsPortalEnabled = True and IsActive = True.
    This is the INVERSE of disable_partner_user_via_api.

    Args:
        sf: Authenticated Salesforce connection
        user_id: User ID to enable/reactivate

    Returns:
        dict: Operation result with status and message
    """
    try:
        # Query user information
        user_query = (
            "SELECT Id, Username, Email, IsActive, IsPortalEnabled, UserType "
            f"FROM User WHERE Id = '{user_id}'"
        )
        user_result = sf.query(user_query)

        if user_result.get('totalSize', 0) == 0:
            logger.warning("User not found: %s", user_id)
            return {
                'success': False,
                'message': f'Usuário não encontrado: {user_id}',
                'user_id': user_id
            }

        user_record = user_result['records'][0]

        # GUARD DO T1 (achado T1-03, 2026-09-09) — esta função LIGA o portal
        # (`IsPortalEnabled=True`) e só pode agir sobre quem já é PowerPartner.
        #
        # Antes do T1 ela nunca alcançava um User Standard: os três chamadores
        # dependem de `is_eligible_partner`, que era falso para papel em branco.
        # Com a derivação, um Standard vira alcançável — e o guard da D[6], que
        # mora em `reconcile_salesforce_access_role`, NÃO cobre nenhum dos três
        # sítios (dois dentro de `enable_partner_user`, um dentro de
        # `reactivate_partner_user`, que sequer lê `UserType`).
        #
        # Caso nomeado, medido em 2026-09-09: employee 870, Vitória Luiza,
        # INATIVA, Prospecção/Assessor Comercial, papel em branco, User Standard
        # com profile 'TI' e Contact válido. Reativá-la no cadastro passaria a
        # ligar o portal na licença interna dela.
        #
        # Converter Standard em Partner é trabalho de
        # `reconcile_salesforce_access_role`, que estaciona o Username, cria um
        # User novo e exige papel explícito. Aqui a recusa é sempre correta.
        user_type = user_record.get('UserType')
        if user_type != 'PowerPartner':
            logger.warning(
                "Reativação de portal RECUSADA para %s: UserType=%r não é PowerPartner",
                user_id, user_type,
            )
            return {
                'success': False,
                'message': (
                    f'Reativação de portal recusada: o User {user_id} é '
                    f'{user_type!r}, não PowerPartner. Licença interna não é '
                    'convertida por elegibilidade derivada.'
                ),
                'user_id': user_id,
                'standard_user_preserved': True,
            }
        username = user_record['Username']
        email = user_record['Email']
        is_active = user_record.get('IsActive', False)
        is_portal_enabled = user_record.get('IsPortalEnabled', False)

        logger.info(
            "🔍 User status before enable: %s (IsActive: %s, IsPortalEnabled: %s)",
            username, is_active, is_portal_enabled)

        # Se já está ativo, nada a fazer
        if is_active and is_portal_enabled:
            logger.info("✅ User already active: %s", username)
            return {
                'success': True,
                'message': f'Usuário {username} já está ativo',
                'user_id': user_id,
                'username': username,
                'email': email
            }

        # Ativar o usuário
        updates = {'IsActive': True, 'IsPortalEnabled': True}

        sf.User.update(user_id, updates)  # type: ignore

        logger.info("✅ Partner User ENABLED: %s (email: %s, ID: %s)", username,
                    email, user_id)

        return {
            'success': True,
            'message': f'Partner User {username} reativado com sucesso',
            'user_id': user_id,
            'username': username,
            'email': email
        }

    except Exception as e:
        error_msg = f"Erro ao reativar Partner User: {e}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg, 'user_id': user_id}


def disable_partner_user_via_api(sf: Salesforce, contact_id: str,
                                 user_id: str) -> Dict[str, Any]:
    """
    Disable a Partner User by setting IsPortalEnabled = False and IsActive = False.
    This is the reliable method that works 100%.

    Args:
        sf: Authenticated Salesforce connection
        contact_id: Contact ID associated with the Partner User
        user_id: User ID to disable

    Returns:
        dict: Operation result with status and message
    """
    try:
        # Query user information
        user_query = f"SELECT Id, Username, Email, IsActive, IsPortalEnabled FROM User WHERE Id = '{user_id}'"
        user_result = sf.query(user_query)

        if user_result.get('totalSize', 0) == 0:
            logger.warning("User not found: %s", user_id)
            return {
                'success': False,
                'message': f'Usuário não encontrado: {user_id}',
                'user_id': user_id
            }

        user_record = user_result['records'][0]
        username = user_record['Username']
        email = user_record['Email']
        is_active = user_record.get('IsActive', True)
        is_portal_enabled = user_record.get('IsPortalEnabled', False)

        logger.info(
            "🔍 User status before disable: %s (IsActive: %s, IsPortalEnabled: %s)",
            username, is_active, is_portal_enabled)

        # Prepare updates needed
        updates_needed = {}

        if is_active:
            updates_needed['IsActive'] = False

        if is_portal_enabled:
            updates_needed['IsPortalEnabled'] = False

        if not updates_needed:
            logger.info("✅ Partner User %s already disabled", username)
            return {
                'success': True,
                'message': f'Partner User {username} já está desabilitado',
                'user_id': user_id,
                'username': username,
                'email': email
            }

        # Update user - THIS METHOD WORKS 100%!
        sf.User.update(user_id, updates_needed)  # type: ignore

        fields_updated = ', '.join(updates_needed.keys())
        logger.info("✅ Partner User %s disabled successfully (%s)", username,
                    fields_updated)

        return {
            'success': True,
            'message':
            f'Partner User {username} desabilitado com sucesso ({fields_updated})',
            'user_id': user_id,
            'username': username,
            'email': email
        }

    except Exception as e:
        error_msg = f"Erro ao desabilitar Partner User {user_id}: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg, 'user_id': user_id}


def deactivate_user_in_salesforce(salesforce_user_id: str, employee_name: str,
                                  employee_email: str,
                                  partner_only: bool = False) -> Dict[str, Any]:
    """
    Deactivate a user in Salesforce.
    For Partner Users, uses DisablePartnerUser API.
    For regular users, sets IsActive = False.
    """
    try:
        sf = get_salesforce_connection()
        if not sf:
            return {
                'success': False,
                'message': 'Falha ao conectar com Salesforce'
            }

        # First, check if user exists and get information
        user_query = (
            "SELECT Id, Username, Email, IsActive, ContactId, "
            f"IsPortalEnabled, UserType FROM User WHERE Id = '{salesforce_user_id}'"
        )
        user_result = sf.query(user_query)

        if user_result.get('totalSize', 0) == 0:
            logger.warning("User not found for User ID: %s", salesforce_user_id)
            return {
                'success': False,
                'message':
                f'Usuário não encontrado para o User ID: {salesforce_user_id}',
                'user_id': salesforce_user_id
            }

        user_record = user_result['records'][0]
        username = user_record['Username']
        email = user_record['Email']
        is_active = user_record['IsActive']
        contact_id = user_record.get('ContactId')
        is_portal_enabled = user_record.get('IsPortalEnabled', False)
        user_type = user_record.get('UserType')

        # Mudança de lotação nunca pode desativar um User interno. O caminho de
        # demissão continua usando partner_only=False e mantém a regra anterior;
        # o caminho de perda de elegibilidade só aceita PowerPartner.
        if partner_only and user_type != 'PowerPartner':
            logger.error(
                "Recusada desativação por elegibilidade: User %s é %s, não PowerPartner",
                salesforce_user_id,
                user_type,
            )
            return {
                'success': False,
                'message': (
                    f'Usuário Salesforce {salesforce_user_id} não é PowerPartner; '
                    'nenhuma desativação foi executada'
                ),
                'user_id': salesforce_user_id,
                'error_code': 'NOT_A_PARTNER_USER',
            }

        logger.info(
            "🔍 User info: %s (email: %s, active: %s, portal: %s, contact: %s)",
            username, email, is_active, is_portal_enabled, contact_id)

        # If it's a Partner User, check if it needs to be disabled
        if is_portal_enabled and contact_id:
            # Verify if Partner User is still active in portal
            partner_query = f"SELECT Id, IsActive, IsPortalEnabled FROM User WHERE Id = '{salesforce_user_id}' AND IsPortalEnabled = true"
            partner_result = sf.query(partner_query)

            if partner_result.get('totalSize', 0) > 0:
                logger.info("🔧 Disabling Partner User for %s", username)
                return disable_partner_user_via_api(sf, contact_id,
                                                    salesforce_user_id)
            else:
                logger.info("✅ Partner User %s already disabled", username)
                return {
                    'success': True,
                    'message': f'Partner User {username} já está desabilitado',
                    'user_id': salesforce_user_id,
                    'username': username,
                    'email': email
                }

        # Check if regular user is already inactive
        if not is_active:
            logger.info("✅ User %s already inactive", username)
            return {
                'success': True,
                'message': f'Usuário {username} já está inativo',
                'user_id': salesforce_user_id,
                'username': username,
                'email': email
            }

        # For regular users, deactivate normally
        sf.User.update(salesforce_user_id, {'IsActive': False})  # type: ignore

        logger.info("✅ User deactivated in Salesforce: %s (%s) - ID: %s",
                    employee_name, employee_email, salesforce_user_id)

        return {
            'success': True,
            'message': f'Usuário {employee_name} desativado no Salesforce'
        }

    except Exception as e:
        error_msg = f"Erro ao desativar usuário no Salesforce: {e}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}


def reactivate_partner_user(contact_id: str,
                            salesforce_user_id: str,
                            employee_name: str,
                            employee_email: str,
                            area: Optional[str] = None,
                            team: Optional[str] = None) -> Dict[str, Any]:
    """
    Reactivate an existing Partner User in Salesforce.

    Para Partner Users, não é possível simplesmente setar IsActive=True.
    É necessário usar a API SetPortalUser ou criar um novo usuário.
    """
    try:
        sf = get_salesforce_connection()
        if not sf:
            return {
                'success': False,
                'message': 'Falha ao conectar com Salesforce'
            }

        # Check if user exists and get current status
        user_query = f"SELECT Id, Username, Email, IsActive, IsPortalEnabled, ContactId FROM User WHERE Id = '{salesforce_user_id}'"
        user_result = sf.query(user_query)

        if user_result.get('totalSize', 0) == 0:
            logger.warning("User not found for User ID: %s", salesforce_user_id)
            return {
                'success': False,
                'message':
                f'Usuário não encontrado para o User ID: {salesforce_user_id}',
                'user_id': salesforce_user_id
            }

        user_record = user_result['records'][0]
        username = user_record['Username']
        is_active = user_record['IsActive']
        is_portal_enabled = user_record.get('IsPortalEnabled', False)

        logger.info("🔍 Checking user: %s (email: %s, active: %s, portal: %s)",
                    username, employee_email, is_active, is_portal_enabled)

        # If already active, nothing to do
        if is_active:
            logger.info("✅ User %s already active", username)
            return {
                'success': True,
                'message': f'Partner User {employee_name} já está ativo',
                'user_id': salesforce_user_id,
                'username': username
            }

        # Fase 2.3 (2026-07-01): reativação DIRETA via enable_partner_user_via_api
        # (IsActive + IsPortalEnabled juntos) — o único caminho que o SF aceita
        # p/ Portal Users. O desvio antigo por enable_partner_user tentava
        # IsActive isolado (bloqueado) e reportava sucesso com user inativo.
        reactivation = enable_partner_user_via_api(sf, salesforce_user_id)
        if reactivation.get('success'):
            logger.info("✅ Partner User reativado via API: %s (%s) - ID: %s",
                        employee_name, employee_email, salesforce_user_id)
            return {
                'success': True,
                'message': f'Partner User {employee_name} reativado no Salesforce',
                'user_id': salesforce_user_id,
                'username': username
            }
        return {
            'success': False,
            'message': (
                f"Falha ao reativar Partner User {employee_name}: "
                f"{reactivation.get('message')} — pode exigir reativação manual "
                "(Contact > Enable Partner User)"
            ),
            'needs_manual_reactivation': True,
            'user_id': salesforce_user_id,
        }

    except Exception as e:
        error_msg = f"Erro ao reativar Partner User no Salesforce: {e}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}


def update_salesforce_user_ramal(sf: Salesforce,
                                 salesforce_user_id: str,
                                 device_id: int,
                                 phone_extension: str,
                                 employee_name: Optional[str] = None) -> bool:
    """
    Atualiza os campos DWRamal__c e DWDeviceId__c no Salesforce User.
    Envia notificação ao Teams quando um ramal é atribuído.

    Args:
        sf: Instância autenticada do Salesforce
        salesforce_user_id: ID do usuário no Salesforce (005...)
        device_id: ID do dispositivo
        phone_extension: Número do ramal
        employee_name: Nome do colaborador (opcional, para notificação Teams)

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        logger.info(
            f"🔍 [SF RAMAL] update_salesforce_user_ramal chamado: "
            f"user_id={salesforce_user_id}, device_id={device_id}, extension={phone_extension}, name={employee_name}"
        )

        if not salesforce_user_id or not str(salesforce_user_id).strip():
            logger.warning(
                "⚠️ [SF RAMAL] Salesforce User ID vazio, não é possível atualizar ramal no Salesforce"
            )
            return False

        # Atualizar os campos customizados no User
        update_data = {
            'DWRamal__c': str(phone_extension),
            'DWDeviceId__c': str(device_id)
        }

        logger.info(f"🔄 [SF RAMAL] Dados para atualização: {update_data}")
        logger.info(
            f"🔄 [SF RAMAL] Executando sf.User.update({salesforce_user_id}, {update_data})"
        )

        sf.User.update(salesforce_user_id, update_data)  # type: ignore

        logger.info(
            f"✅ [SF RAMAL] Ramal {phone_extension} sincronizado no Salesforce User {salesforce_user_id}"
        )

        # Enviar notificação ao Teams
        if employee_name:
            send_teams_notification(employee_name, device_id, phone_extension)
        else:
            logger.warning(
                "⚠️ [SF RAMAL] Nome do colaborador não fornecido, notificação Teams não enviada"
            )

        return True

    except Exception as e:
        logger.error(
            f"❌ [SF RAMAL] Erro ao atualizar ramal no Salesforce: {e}",
            exc_info=True)
        return False


def clear_salesforce_user_ramal(sf: Salesforce,
                                salesforce_user_id: str) -> bool:
    """
    Limpa os campos DWRamal__c e DWDeviceId__c no Salesforce User.

    Args:
        sf: Instância autenticada do Salesforce
        salesforce_user_id: ID do usuário no Salesforce (005...)

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        logger.info(
            f"🔍 [SF RAMAL CLEAR] clear_salesforce_user_ramal chamado: user_id={salesforce_user_id}"
        )

        if not salesforce_user_id or not str(salesforce_user_id).strip():
            logger.warning(
                "⚠️ [SF RAMAL CLEAR] Salesforce User ID vazio, não é possível limpar ramal no Salesforce"
            )
            return False

        # Limpar os campos customizados no User
        update_data = {'DWRamal__c': None, 'DWDeviceId__c': None}

        logger.info(f"🔄 [SF RAMAL CLEAR] Dados para limpeza: {update_data}")
        logger.info(
            f"🔄 [SF RAMAL CLEAR] Executando sf.User.update({salesforce_user_id}, {update_data})"
        )

        sf.User.update(salesforce_user_id, update_data)  # type: ignore

        logger.info(
            f"✅ [SF RAMAL CLEAR] Ramal removido do Salesforce User {salesforce_user_id}"
        )
        return True

    except Exception as e:
        logger.error(
            f"❌ [SF RAMAL CLEAR] Erro ao limpar ramal no Salesforce: {e}",
            exc_info=True)
        return False


def update_contact_account(salesforce_contact_id: str, new_team: str,
                           employee_name: str) -> Dict[str, Any]:
    """
    Update Contact AccountId in Salesforce based on team.
    """
    try:
        if not salesforce_contact_id or not str(salesforce_contact_id).strip():
            return {'success': False, 'message': 'Contact ID é obrigatório'}

        if not new_team:
            return {'success': False, 'message': 'Novo time é obrigatório'}

        new_account_id = resolve_team_account_id(new_team)

        if not new_account_id:
            logger.warning(
                "Time '%s' não possui mapeamento para Account do Salesforce",
                new_team)
            return {
                'success':
                False,
                'message':
                f"Time '{new_team}' não possui mapeamento para Account no Salesforce"
            }

        sf = get_salesforce_connection()
        if not sf:
            return {
                'success': False,
                'message': 'Falha na autenticação com o Salesforce'
            }

        try:
            # Idempotente: sem esta leitura, o mesmo Contact era reescrito a cada
            # edição de perfil/área que reconcilia o time, e a falha de uma
            # edição anterior nunca era reparada sem mexer em outro campo.
            current = sf.query(
                f"SELECT Id, AccountId FROM Contact "
                f"WHERE Id = '{_esc_soql(str(salesforce_contact_id).strip())}' LIMIT 1"
            )
            current_records = current.get('records') or []
            if current_records and current_records[0].get('AccountId') == new_account_id:
                return {
                    'success': True,
                    'executed': False,
                    'message': f"Contact já está no Account do time '{new_team}'",
                    'account_id': new_account_id,
                }

            sf.Contact.update(salesforce_contact_id,
                              {'AccountId': new_account_id})  # type: ignore

            success_message = (
                f"AccountId do Contact atualizado para o time '{new_team}' "
                f"(Account ID: {new_account_id})")
            logger.info(success_message)
            return {
                'success': True,
                'executed': True,
                'message': success_message,
                'account_id': new_account_id
            }

        except Exception as sf_error:
            error_message = f"Erro ao atualizar Contact no Salesforce: {str(sf_error)}"
            logger.error(error_message)
            return {'success': False, 'message': error_message}

    except Exception as e:
        error_msg = f"Erro na atualização do AccountId do Contact: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}


# Profile IDs adicionais para Portal Users
PROFILE_HEAD_ID = '00eU500000EVAKoIAP'  # Portal - Head (PowerPartner)
PROFILE_ESPECIALISTAS_ID = '00eU500000DjcfyIAB'  # Portal - Especialistas (PowerPartner)


def determine_salesforce_profile(employee_data: Dict[str, Any]) -> tuple:
    """
    Determina o perfil Salesforce do colaborador — WRAPPER do resolvedor ÚNICO.

    Fase 1 (2026-07-01): a lógica heurística antiga (level/position/sector/
    company, que IGNORAVA is_leader — o discriminador real de Head, 9/9
    empírico — e não cobria Portal - Pessoa Jurídica) foi substituída pela
    tabela empírica em eligibility.resolve_salesforce_profile_name, a MESMA
    usada no create e na reativação. O Id NÃO é retornado aqui — resolver por
    Name via get_profile_id_by_name(sf, name) no chamador (nunca hardcode).

    Returns:
        tuple: (profile_id=None, profile_name, is_eligible)
    """
    profile_name = resolve_salesforce_profile_name(
        area=employee_data.get('area'),
        team=employee_data.get('team'),
        is_leader=bool(employee_data.get('is_leader')),
        position=employee_data.get('position'),
        salesforce_access_role=employee_data.get('salesforce_access_role'),
    )
    logger.info(
        "🔍 determine_salesforce_profile (resolvedor único): area=%r team=%r "
        "position=%r is_leader=%r -> %r",
        employee_data.get('area'), employee_data.get('team'),
        employee_data.get('position'), employee_data.get('is_leader'), profile_name,
    )
    return (None, profile_name, profile_name is not None)


def update_user_profile_for_area_change(
    salesforce_user_id: str,
    employee_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Atualiza o ProfileId de um usuário no Salesforce quando os dados do colaborador mudam.

    Usa a função determine_salesforce_profile para determinar o perfil correto baseado em:
    - Portal - Head (prioridade 1)
    - Portal - Especialistas (prioridade 2)
    - Portal - SDR (prioridade 3)
    - Portal - Assessor (prioridade 4)

    Args:
        salesforce_user_id: ID do usuário no Salesforce (005...)
        employee_data: Dict com todos os campos do colaborador

    Returns:
        dict: {success: bool, message: str, profile_name: str (se sucesso)}
    """
    try:
        if not salesforce_user_id or not str(salesforce_user_id).strip():
            return {'success': False, 'message': 'User ID do Salesforce é obrigatório'}

        sf = get_salesforce_connection()
        if not sf:
            notify_teams_salesforce_error(
                "Falha na autenticacao com o Salesforce",
                operation="Atualizar ProfileId Salesforce",
            )
            return {'success': False, 'message': 'Falha na autenticação com o Salesforce'}

        # Determinar o perfil pelo resolvedor único e resolver o Id por NAME
        _, target_profile_name, is_eligible = determine_salesforce_profile(employee_data)

        if not is_eligible or not target_profile_name:
            return {'success': False, 'message': 'Colaborador não elegível para Partner User'}

        new_profile_id = get_profile_id_by_name(sf, target_profile_name)
        if not new_profile_id:
            return {'success': False,
                    'message': f"Profile '{target_profile_name}' não encontrado no Salesforce"}

        # Verificar o perfil atual do usuário
        user_query = f"SELECT Id, ProfileId, Profile.Name FROM User WHERE Id = '{salesforce_user_id}'"
        user_result = sf.query(user_query)

        if user_result.get('totalSize', 0) == 0:
            notify_teams_salesforce_error(
                f"Usuario {salesforce_user_id} nao encontrado no Salesforce",
                operation="Atualizar ProfileId Salesforce",
            )
            return {'success': False, 'message': f"Usuário {salesforce_user_id} não encontrado no Salesforce"}

        current_profile_name = user_result['records'][0].get('Profile', {}).get('Name', 'Desconhecido')

        if current_profile_name == target_profile_name:
            return {
                'success': True,
                'message': f"Usuário já possui o perfil '{target_profile_name}'",
                'profile_name': target_profile_name
            }

        # Atualizar o ProfileId do usuário
        try:
            sf.User.update(salesforce_user_id, {'ProfileId': new_profile_id})  # type: ignore

            success_message = f"Perfil do usuário atualizado de '{current_profile_name}' para '{target_profile_name}'"
            logger.info(f"✅ {success_message}")
            return {'success': True, 'message': success_message, 'profile_name': target_profile_name}

        except Exception as sf_error:
            error_message = f"Erro ao atualizar ProfileId do usuário: {str(sf_error)}"
            logger.error(f"❌ {error_message}")
            notify_teams_salesforce_error(
                error_message,
                operation="Atualizar ProfileId Salesforce",
            )
            return {'success': False, 'message': error_message}

    except Exception as e:
        error_msg = f"Erro na atualização do perfil do usuário: {str(e)}"
        logger.error(f"❌ {error_msg}")
        notify_teams_salesforce_error(
            error_msg,
            operation="Atualizar ProfileId Salesforce",
        )
        return {'success': False, 'message': error_msg}


# ---------------------------------------------------------------------------
# Papel (UserRole) do Partner User no Salesforce
#
# O Salesforce tem DOIS campos distintos no User: o Perfil (Profile, genérico
# por família) e o Papel (UserRole, a hierarquia do time — "Faz Capital - Team
# X Usuário/Gerente de Parceiro"). O MakersHub só reconciliava o Perfil; trocar
# o time deixava o usuário preso no Papel do time antigo. Medido em 2026-10-06:
# o colaborador 952 virou Closer, o Perfil mudou para "Portal - Assessor", mas
# o Papel continuou "Faz Capital - Team SDR Usuário de Parceiro" e o Contact
# continuou no Account "Faz Capital - Team SDR" (FBI-4842).
#
# A base do nome do UserRole é EXATAMENTE o nome do Account do time, então a
# base é resolvida pelo Account já mapeado (fonte única — nunca uma segunda
# tabela de nomes que envelhece). O sufixo vem de `is_leader`. O sufixo
# "Executivo deParceiro" é um entitlement do Salesforce que o RH não modela:
# é preservado quando já está no usuário, nunca inventado.
# ---------------------------------------------------------------------------

USER_ROLE_SUFFIX_USER = "Usuário de Parceiro"
USER_ROLE_SUFFIX_MANAGER = "Gerente de Parceiro"
USER_ROLE_SUFFIX_EXECUTIVE = "Executivo deParceiro"


def _join_messages(*messages: Optional[str]) -> str:
    """Concatena mensagens não vazias com '; ', sem ';' sobrando nas pontas."""
    return "; ".join(m.strip().strip("; ") for m in messages if m and m.strip())


_ACCOUNT_NAME_CACHE: Dict[str, str] = {}
_USER_ROLE_ID_CACHE: Dict[str, str] = {}
_USER_ROLE_FAMILY_CACHE: Dict[str, bool] = {}


def get_account_name_by_id(sf: Salesforce, account_id: str) -> Optional[str]:
    """Nome do Account por Id, com cache por processo (base do UserRole)."""
    if not account_id:
        return None
    cached = _ACCOUNT_NAME_CACHE.get(account_id)
    if cached:
        return cached
    try:
        safe_id = _esc_soql(account_id)
        result = sf.query(f"SELECT Id, Name FROM Account WHERE Id = '{safe_id}'")
        records = result.get('records') or []
        if records:
            name = records[0].get('Name')
            if name:
                _ACCOUNT_NAME_CACHE[account_id] = name
                return name
    except Exception as e:
        logger.error("Erro ao resolver Account %s: %s", account_id, e)
    return None


def team_has_user_role_family(sf: Salesforce, base: str) -> bool:
    """True quando existe ao menos um UserRole com a base do time no Salesforce.

    Separa "este time não tem família de Papel" (não aplicável — ex.: XP
    Internacional, cujo Account não tem UserRole) de "o sufixo alvo sumiu"
    (falha real). Sem isto, um time sem papel viraria falha barulhenta na
    timeline a cada edição.
    """
    if not base:
        return False
    cached = _USER_ROLE_FAMILY_CACHE.get(base)
    if cached is not None:
        return cached
    try:
        safe_base = _esc_soql(base)
        result = sf.query(
            f"SELECT Id FROM UserRole WHERE Name LIKE '{safe_base} %' LIMIT 1"
        )
        exists = result.get('totalSize', 0) > 0
    except Exception as e:
        logger.error("Erro ao resolver a família de UserRole '%s': %s", base, e)
        exists = False
    _USER_ROLE_FAMILY_CACHE[base] = exists
    return exists


def resolve_team_user_role_base(sf: Salesforce, team: Optional[str]) -> Optional[str]:
    """Base do UserRole do time = nome do Account do time (fonte única).

    `None` quando o time não é destino mapeado ou quando o Account não tem
    nenhuma família de UserRole no Salesforce.
    """
    account_id = resolve_team_account_id(team)
    if not account_id:
        return None
    base = get_account_name_by_id(sf, account_id)
    if not base or not team_has_user_role_family(sf, base):
        return None
    return base


def get_user_role_id_by_name(sf: Salesforce, role_name: str) -> Optional[str]:
    """Resolve o Id de um UserRole pelo Name, com cache por processo."""
    if not role_name:
        return None
    cached = _USER_ROLE_ID_CACHE.get(role_name)
    if cached:
        return cached
    try:
        safe_name = _esc_soql(role_name)
        result = sf.query(f"SELECT Id FROM UserRole WHERE Name = '{safe_name}'")
        if result.get('totalSize', 0) > 0:
            role_id = result['records'][0]['Id']
            _USER_ROLE_ID_CACHE[role_name] = role_id
            return role_id
        logger.error("UserRole '%s' não encontrado no Salesforce", role_name)
        return None
    except Exception as e:
        logger.error("Erro ao resolver UserRole '%s': %s", role_name, e)
        return None


def _current_user_role_suffix(current_role_name: Optional[str]) -> Optional[str]:
    """Sufixo de nível do UserRole atual (Usuário/Gerente/Executivo), ou None."""
    if not current_role_name:
        return None
    for suffix in (
        USER_ROLE_SUFFIX_EXECUTIVE,
        USER_ROLE_SUFFIX_MANAGER,
        USER_ROLE_SUFFIX_USER,
    ):
        if current_role_name.endswith(suffix):
            return suffix
    return None


def resolve_salesforce_user_role_name(
    sf: Salesforce,
    team: Optional[str],
    is_leader: bool,
    current_role_name: Optional[str] = None,
) -> Optional[str]:
    """Nome do UserRole alvo do time, ou None quando o time não tem papel.

    Troca a BASE do papel (o time) e PRESERVA o nível atual (Usuário/Gerente/
    Executivo). Medido em 2026-10-06: o nível não é derivável de forma confiável
    do RH — há Gerente e Executivo com Perfil "Portal - Assessor" e
    "Portal - Especialistas", e rebaixá-los na troca de time seria um efeito
    colateral que ninguém pediu. `is_leader` só decide quando não há nível
    atual (ex.: papel nulo).
    """
    base = resolve_team_user_role_base(sf, team)
    if not base:
        return None
    suffix = _current_user_role_suffix(current_role_name)
    if suffix is None:
        suffix = USER_ROLE_SUFFIX_MANAGER if is_leader else USER_ROLE_SUFFIX_USER
    return f"{base} {suffix}"


def update_salesforce_user_role(
    salesforce_user_id: str,
    employee_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Reconcilia o UserRole (Papel) do Partner User com o time do MakersHub.

    Idempotente: não escreve quando o papel já é o alvo. Time sem mapeamento
    não é erro (papel preservado); papel alvo inexistente no Salesforce é
    falha explícita, sem tocar no usuário.
    """
    try:
        if not salesforce_user_id or not str(salesforce_user_id).strip():
            return {'success': False, 'message': 'User ID do Salesforce é obrigatório'}

        sf = get_salesforce_connection()
        if not sf:
            return {'success': False, 'message': 'Falha na autenticação com o Salesforce'}

        user_id = _validate_sf_id(salesforce_user_id)
        current_result = sf.query(
            f"SELECT Id, UserRole.Name FROM User WHERE Id = '{user_id}' LIMIT 1"
        )
        records = current_result.get('records') or []
        if not records:
            return {
                'success': False,
                'message': f"Usuário {user_id} não encontrado no Salesforce",
            }

        current_role_name = (records[0].get('UserRole') or {}).get('Name')
        target_role_name = resolve_salesforce_user_role_name(
            sf,
            employee_data.get('team'),
            bool(employee_data.get('is_leader')),
            current_role_name,
        )
        if not target_role_name:
            return {
                'success': True,
                'executed': False,
                'message': (
                    "Time sem Papel (UserRole) mapeado no Salesforce; papel preservado"
                ),
                'user_role_name': current_role_name,
            }
        if current_role_name == target_role_name:
            return {
                'success': True,
                'executed': False,
                'message': f"Usuário já possui o papel '{target_role_name}'",
                'user_role_name': target_role_name,
            }

        role_id = get_user_role_id_by_name(sf, target_role_name)
        if not role_id:
            return {
                'success': False,
                'message': f"Papel '{target_role_name}' não encontrado no Salesforce",
            }

        sf.User.update(user_id, {'UserRoleId': role_id})  # type: ignore
        message = (
            f"Papel do usuário atualizado de '{current_role_name}' "
            f"para '{target_role_name}'"
        )
        logger.info("✅ %s", message)
        return {
            'success': True,
            'executed': True,
            'message': message,
            'user_role_name': target_role_name,
        }
    except Exception as e:
        error_msg = f"Erro ao atualizar o papel do usuário: {str(e)}"
        logger.error("❌ %s", error_msg)
        notify_teams_salesforce_error(
            error_msg, operation="Atualizar UserRole Salesforce"
        )
        return {'success': False, 'message': error_msg}


# Small serial batches: the FazTotalCustodiaAccountNucleoFamiliar flow writes the
# parent account and its children, and parallel batches fight over the same
# record (UNABLE_TO_LOCK_ROW).
RESTAMP_BATCH_SIZE = 50
_RESTAMP_OBJECTS = (('Account', 'accounts'), ('Opportunity', 'opportunities'))


def restamp_owner_team_sharing(
    salesforce_user_id: str,
    *,
    apply: bool = True,
    batch_size: int = RESTAMP_BATCH_SIZE,
) -> Dict[str, Any]:
    """Rewrite the sharing of the owner's Accounts and Opportunities with their current team.

    The sharing rules read `TimeAssessoresRegrasCompartilhamento__c`, which the
    `Faz_*_After_Create_Update_Time_da_Conta_Proprietario` flows copy from
    `Owner.DWTeam__c` only when the Account or Opportunity is saved. Saving the
    User does not rewrite the portfolio (FBI-4842, live test on 2026-10-06):
    without this step, whoever changes team keeps the portfolio shared with the
    old team.

    The value written is the `DWTeam__c` read from Salesforce, the same one the
    flow writes. Idempotent: it only touches a record whose value differs.
    `apply=False` only counts.
    """
    action = 'Recarimbo de compartilhamento'
    counts: Dict[str, Any] = {
        key: {'pending': 0, 'updated': 0, 'failed': []}
        for _, key in _RESTAMP_OBJECTS
    }
    try:
        if not salesforce_user_id or not str(salesforce_user_id).strip():
            return {'success': False, 'executed': False,
                    'message': 'User ID do Salesforce é obrigatório', **counts}

        sf = get_salesforce_connection()
        if not sf:
            return {'success': False, 'executed': False,
                    'message': 'Falha na autenticação com o Salesforce', **counts}

        user_id = _validate_sf_id(str(salesforce_user_id).strip())
        user_result = sf.query(
            f"SELECT Id, IsActive, DWTeam__c FROM User WHERE Id = '{user_id}' LIMIT 1"
        )
        records = user_result.get('records') or []
        if not records:
            return {'success': True, 'executed': False,
                    'message': f'Usuário {user_id} não encontrado; compartilhamento não alterado',
                    **counts}
        if not records[0].get('IsActive'):
            return {'success': True, 'executed': False,
                    'message': 'Usuário inativo; compartilhamento não alterado', **counts}
        team = (records[0].get('DWTeam__c') or '').strip()
        if not team:
            # Never write an empty value: it would drop the sharing of the whole portfolio.
            return {'success': True, 'executed': False,
                    'message': 'Usuário sem time no Salesforce; compartilhamento não alterado',
                    **counts}

        safe_team = _esc_soql(team)
        for sobject, key in _RESTAMP_OBJECTS:
            pending = sf.query_all(
                f"SELECT Id FROM {sobject} WHERE OwnerId = '{user_id}' "
                f"AND ({SHARING_FIELD} != '{safe_team}' OR {SHARING_FIELD} = null)"
            ).get('records') or []
            counts[key]['pending'] = len(pending)
            if not apply or not pending:
                continue
            payload = [{'Id': row['Id'], SHARING_FIELD: team} for row in pending]
            results = getattr(sf.bulk, sobject).update(
                payload, batch_size=batch_size, use_serial=True
            )
            for row, outcome in zip(payload, results):
                if outcome.get('success'):
                    counts[key]['updated'] += 1
                else:
                    counts[key]['failed'].append(
                        {'id': row['Id'], 'errors': outcome.get('errors')}
                    )

        failed_total = sum(len(counts[key]['failed']) for _, key in _RESTAMP_OBJECTS)
        if apply:
            message = (
                f"Compartilhamento: {counts['accounts']['updated']} contas e "
                f"{counts['opportunities']['updated']} oportunidades atualizadas para '{team}'"
            )
        else:
            message = (
                f"Compartilhamento: {counts['accounts']['pending']} contas e "
                f"{counts['opportunities']['pending']} oportunidades a atualizar para '{team}'"
            )
        if failed_total:
            message += f"; {failed_total} registro(s) recusado(s) pelo Salesforce"
            notify_teams_salesforce_error(f"{message} (User {user_id})", operation=action)
        logger.info("%s (User %s)", message, user_id)
        return {'success': failed_total == 0, 'executed': apply, 'team': team,
                'message': message, **counts}
    except Exception as e:
        error_msg = f"Erro ao recarimbar compartilhamento: {str(e)}"
        logger.error("❌ %s", error_msg)
        notify_teams_salesforce_error(error_msg, operation=action)
        return {'success': False, 'executed': apply, 'message': error_msg, **counts}


def sync_salesforce_user_fields(
    salesforce_user_id: str,
    employee_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Sincroniza campos do colaborador com o User no Salesforce.

    Mapeamento de campos:
    - advisor_code    -> User.DWCodigoAssessorXP__c
    - team            -> User.DWTeam__c (token do flow para time de parceiro;
                         ver dwteam_value_for_team, FBI-4842)
    - phone_extension -> User.DWRamal__c
    - device_id       -> User.DWDeviceId__c
    - sector          -> User.Department
    - business_unit   -> User.Division

    `squad` is NOT synced (FBI-4842, gap 3): the Salesforce `DWSquad__c` holds
    squads the registration does not have (Redbull, Bayside, Harlem, Okinawa,
    Kips Bay, 808, Matsumoto, Time Integral) and MakersHub is not their source.
    Writing the registration `squad` would overwrite the Salesforce value with an
    empty or unmatched one. The field keeps existing in the registration for
    internal use.

    Args:
        salesforce_user_id: ID do User no Salesforce (005...)
        employee_data: Dict com dados do colaborador

    Returns:
        dict: {'success': bool, 'message': str, 'updated_fields': list}
    """
    try:
        if not salesforce_user_id or not str(salesforce_user_id).strip() or str(salesforce_user_id).strip() == '0':
            notify_teams_salesforce_error(
                "Salesforce User ID nao fornecido ou invalido",
                operation="Sync Salesforce User Fields",
            )
            return {'success': False, 'message': 'Salesforce User ID não fornecido ou inválido', 'updated_fields': []}

        salesforce_user_id = str(salesforce_user_id).strip()

        sf = get_salesforce_connection()
        if not sf:
            notify_teams_salesforce_error(
                "Falha na autenticacao com o Salesforce",
                operation="Sync Salesforce User Fields",
            )
            return {'success': False, 'message': 'Falha na autenticação com o Salesforce', 'updated_fields': []}

        # Verificar se o usuário existe
        user_query = f"SELECT Id, IsActive FROM User WHERE Id = '{salesforce_user_id}'"
        user_result = sf.query(user_query)

        if user_result.get('totalSize', 0) == 0:
            notify_teams_salesforce_error(
                f"Usuario {salesforce_user_id} nao encontrado no Salesforce",
                operation="Sync Salesforce User Fields",
            )
            return {'success': False, 'message': f'Usuário {salesforce_user_id} não encontrado no Salesforce', 'updated_fields': []}

        # Montar payload com campos a serem atualizados
        user_data = {}
        updated_fields = []

        # Map fields. `squad` is left OUT on purpose: Salesforce is the source of
        # `DWSquad__c` (FBI-4842, gap 3); see the docstring.
        field_mapping = {
            'advisor_code': 'DWCodigoAssessorXP__c',
            'team': 'DWTeam__c',
            'sector': 'Department',
            'business_unit': 'Division'
        }

        for local_field, sf_field in field_mapping.items():
            value = employee_data.get(local_field)
            if local_field == 'team':
                value = dwteam_value_for_team(value)
            if value is not None and str(value).strip():
                user_data[sf_field] = str(value).strip()
                updated_fields.append(local_field)

        # Adicionar ramal e device_id se disponíveis
        phone_extension = employee_data.get('phone_extension')
        device_id = employee_data.get('device_id')

        if phone_extension:
            user_data['DWRamal__c'] = str(phone_extension)
            updated_fields.append('phone_extension')

        if device_id:
            user_data['DWDeviceId__c'] = str(device_id)
            updated_fields.append('device_id')

        # O Salesforce recusa o registro INTEIRO por um unico valor acima do limite
        # do campo (medido: User.DWCodigoAssessorXP__c aceita 10 caracteres e o
        # cadastro aceita 50). O campo longo e pulado e reportado; os demais seguem.
        user_data, oversized = field_contract.drop_oversized(
            user_data, field_contract.USER_LIMITS
        )
        if oversized:
            skipped_sf = {item.sf_field for item in oversized}
            updated_fields = [
                name for name in updated_fields
                if field_mapping.get(name) not in skipped_sf
            ]
        oversized_message = (
            "Não sincronizado por exceder o limite do campo no Salesforce: "
            + ", ".join(item.describe() for item in oversized)
            if oversized else ""
        )
        oversized_names = [item.sf_field for item in oversized]

        if not user_data:
            if oversized:
                return {
                    'success': False,
                    'message': oversized_message,
                    'updated_fields': [],
                    'skipped_fields': oversized_names,
                }
            return {'success': True, 'message': 'Nenhum campo para atualizar no Salesforce User', 'updated_fields': []}

        # Atualizar User no Salesforce
        try:
            sf.User.update(salesforce_user_id, user_data)  # type: ignore

            success_msg = f"Campos atualizados no Salesforce User: {', '.join(updated_fields)}"
            logger.info(f"✅ {success_msg}")
            return {
                'success': not oversized,
                'message': _join_messages(success_msg, oversized_message),
                'updated_fields': updated_fields,
                'skipped_fields': oversized_names,
            }

        except Exception as sf_error:
            error_msg = f"Erro ao atualizar User no Salesforce: {str(sf_error)}"
            logger.error(f"❌ {error_msg}")
            notify_teams_salesforce_error(
                error_msg,
                operation="Sync Salesforce User Fields",
            )
            return {'success': False, 'message': error_msg, 'updated_fields': []}

    except Exception as e:
        error_msg = f"Erro na sincronização de campos do User: {str(e)}"
        logger.error(f"❌ {error_msg}")
        notify_teams_salesforce_error(
            error_msg,
            operation="Sync Salesforce User Fields",
        )
        return {'success': False, 'message': error_msg, 'updated_fields': []}


# ============================================================================
# DADOS CADASTRAIS E IDENTIDADE (contrato: salesforce_field_contract)
# ============================================================================
# A criacao grava no Contact nome, e-mail, telefones, cargo, nascimento, endereco,
# setor e codigo do assessor, e no User o Username/Email/FederationIdentifier. A
# edicao so reescrevia seis campos do User. As tres funcoes abaixo fecham essa
# diferenca, sempre so com o que MUDOU e sem limpar nada no Salesforce.


def _sync_failure_code(error: Exception) -> str:
    return _extract_sf_error_code(error) or field_contract.safe_error_text(error, 120)


def _isolation_units(payload: Dict[str, str]) -> List[Dict[str, str]]:
    """Divide o payload em unidades que podem falhar sozinhas.

    Cada campo e uma unidade, exceto os de `ATOMIC_GROUPS`: nome (First/Last) e
    endereco so se gravam inteiros.
    """
    units: List[Dict[str, str]] = []
    grouped: set[str] = set()
    for group in field_contract.ATOMIC_GROUPS:
        members = {name: payload[name] for name in group if name in payload}
        if members:
            units.append(members)
            grouped.update(members)
    units.extend({name: value} for name, value in payload.items() if name not in grouped)
    return units


def _update_isolating(record_api: Any, record_id: str, payload: Dict[str, str]):
    """Grava `payload`; se o DML recusar, isola a unidade culpada.

    Um update com varios campos e atomico: um valor invalido derruba todos. Na
    falha, cada unidade (campo, ou grupo atomico) e tentada sozinha (idempotente),
    de modo que um erro num campo nao impeca o e-mail, por exemplo, de chegar ao
    Salesforce. Devolve (campos gravados, {campo: codigo do erro}).
    """
    try:
        record_api.update(record_id, payload)
        return list(payload), {}
    except Exception as bulk_error:  # noqa: BLE001
        units = _isolation_units(payload)
        if len(units) == 1:
            code = _sync_failure_code(bulk_error)
            return [], {name: code for name in units[0]}
    applied: List[str] = []
    failed: Dict[str, str] = {}
    for unit in units:
        try:
            record_api.update(record_id, unit)
            applied.extend(unit)
        except Exception as unit_error:  # noqa: BLE001
            code = _sync_failure_code(unit_error)
            failed.update({name: code for name in unit})
    return applied, failed


def _skipped_message(skipped) -> str:
    if not skipped:
        return ""
    return (
        "Não sincronizado por exceder o limite do campo no Salesforce: "
        + ", ".join(item.describe() for item in skipped)
    )


def _failed_message(kind: str, failed: Dict[str, str]) -> str:
    if not failed:
        return ""
    return f"{kind}: falha ao atualizar " + ", ".join(
        f"{name} ({code})" for name, code in failed.items()
    )


def _record_sync_result(
    *,
    kind: str,
    applied: List[str],
    failed: Dict[str, str],
    skipped,
    already_aligned: bool,
) -> Dict[str, Any]:
    skipped_names = [item.sf_field for item in skipped]
    problems = _join_messages(_failed_message(kind, failed), _skipped_message(skipped))
    if applied:
        message = _join_messages(
            f"{kind} atualizado: {', '.join(applied)}", problems
        )
    elif already_aligned and not problems:
        message = f"{kind} já está alinhado ao cadastro"
    else:
        message = problems or f"Nenhum campo do {kind} para atualizar"
    return {
        'success': not failed and not skipped,
        'executed': bool(applied or failed),
        'message': message,
        'updated_fields': applied,
        'skipped_fields': skipped_names,
        'failed_fields': dict(failed),
    }


def sync_salesforce_contact_fields(
    salesforce_contact_id: Optional[str],
    employee_data: Dict[str, Any],
    changed_fields: Any,
) -> Dict[str, Any]:
    """Segue o Contact aos campos cadastrais que MUDARAM (espelho da criacao).

    Nome, e-mail, telefones, cargo, nascimento, codigo do assessor, endereco e
    setor. `AccountId` (time) tem funcao propria (`update_contact_account`).
    So grava o que difere do Salesforce; valor vazio nunca limpa; valor acima do
    limite do campo e pulado e reportado (ver `salesforce_field_contract`).
    """
    operation = "Sync Salesforce Contact Fields"
    empty: Dict[str, Any] = {
        'success': True, 'executed': False, 'updated_fields': [],
        'skipped_fields': [], 'failed_fields': {},
    }
    try:
        contact_id = str(salesforce_contact_id or '').strip()
        if not contact_id or contact_id == '0':
            return {**empty, 'success': False,
                    'message': 'Contact ID do Salesforce ausente; campos do Contact não sincronizados'}
        plan = field_contract.plan_payload(
            field_contract.CONTACT_RULES,
            employee_data,
            changed_fields,
            field_contract.CONTACT_LIMITS,
        )
        if not plan.payload:
            if plan.skipped:
                return {**empty, 'success': False,
                        'skipped_fields': [item.sf_field for item in plan.skipped],
                        'message': _skipped_message(plan.skipped)}
            return {**empty, 'message': 'Nenhum campo do Contact para atualizar'}

        sf = get_salesforce_connection()
        if not sf:
            notify_teams_salesforce_error(
                "Falha na autenticacao com o Salesforce", operation=operation
            )
            return {**empty, 'success': False, 'executed': True,
                    'message': 'Falha na autenticação com o Salesforce'}

        selected = ', '.join(['Id', *plan.payload])
        current = sf.query(
            f"SELECT {selected} FROM Contact "
            f"WHERE Id = '{_validate_sf_id(contact_id)}' LIMIT 1"
        )
        records = current.get('records') or []
        if not records:
            return {**empty, 'success': False, 'executed': True,
                    'message': f'Contact {contact_id} não encontrado no Salesforce'}
        stored = records[0]
        diff = {
            sf_field: value
            for sf_field, value in plan.payload.items()
            if not field_contract.same_value(sf_field, stored.get(sf_field), value)
        }
        applied: List[str] = []
        failed: Dict[str, str] = {}
        if diff:
            applied, failed = _update_isolating(sf.Contact, contact_id, diff)
        result = _record_sync_result(
            kind="Contact",
            applied=applied,
            failed=failed,
            skipped=plan.skipped,
            already_aligned=not diff,
        )
        if failed:
            notify_teams_salesforce_error(result['message'], operation=operation)
        return result
    except Exception as exc:  # noqa: BLE001
        error_msg = f"Erro na sincronização de campos do Contact: {field_contract.safe_error_text(exc)}"
        logger.error("❌ %s", error_msg)
        notify_teams_salesforce_error(error_msg, operation=operation)
        return {**empty, 'success': False, 'executed': True, 'message': error_msg}


def sync_salesforce_user_name(
    salesforce_user_id: Optional[str],
    employee_data: Dict[str, Any],
    changed_fields: Any,
) -> Dict[str, Any]:
    """Segue o nome do User ao cadastro quando `name` mudou (FirstName/LastName)."""
    operation = "Sync Salesforce User Name"
    empty: Dict[str, Any] = {
        'success': True, 'executed': False, 'updated_fields': [],
        'skipped_fields': [], 'failed_fields': {},
    }
    try:
        user_id = str(salesforce_user_id or '').strip()
        if not user_id or user_id == '0':
            return {**empty, 'success': False,
                    'message': 'User ID do Salesforce ausente; nome do User não sincronizado'}
        plan = field_contract.plan_payload(
            field_contract.USER_NAME_RULES,
            employee_data,
            changed_fields,
            field_contract.USER_LIMITS,
        )
        if not plan.payload:
            if plan.skipped:
                return {**empty, 'success': False,
                        'skipped_fields': [item.sf_field for item in plan.skipped],
                        'message': _skipped_message(plan.skipped)}
            return {**empty, 'message': 'Nenhum nome do User para atualizar'}

        sf = get_salesforce_connection()
        if not sf:
            notify_teams_salesforce_error(
                "Falha na autenticacao com o Salesforce", operation=operation
            )
            return {**empty, 'success': False, 'executed': True,
                    'message': 'Falha na autenticação com o Salesforce'}

        selected = ', '.join(['Id', 'UserType', *plan.payload])
        current = sf.query(
            f"SELECT {selected} FROM User "
            f"WHERE Id = '{_validate_sf_id(user_id)}' LIMIT 1"
        )
        records = current.get('records') or []
        if not records:
            return {**empty, 'success': False, 'executed': True,
                    'message': f'Usuário {user_id} não encontrado no Salesforce'}
        stored = records[0]
        if stored.get('UserType') != field_contract.PARTNER_USER_TYPE:
            return {**empty,
                    'message': 'Nome do User: User não é Partner (gerido fora do MakersHub); nome não alterado'}
        diff = {
            sf_field: value
            for sf_field, value in plan.payload.items()
            if not field_contract.same_value(sf_field, stored.get(sf_field), value)
        }
        applied: List[str] = []
        failed: Dict[str, str] = {}
        if diff:
            applied, failed = _update_isolating(sf.User, user_id, diff)
        result = _record_sync_result(
            kind="Nome do User",
            applied=applied,
            failed=failed,
            skipped=plan.skipped,
            already_aligned=not diff,
        )
        if failed:
            notify_teams_salesforce_error(result['message'], operation=operation)
        return result
    except Exception as exc:  # noqa: BLE001
        error_msg = f"Erro na sincronização do nome do User: {field_contract.safe_error_text(exc)}"
        logger.error("❌ %s", error_msg)
        notify_teams_salesforce_error(error_msg, operation=operation)
        return {**empty, 'success': False, 'executed': True, 'message': error_msg}


def _identity_collisions(
    sf: Any, user_id: str, wanted_email: str
) -> List[Dict[str, Any]]:
    """Outros Users que ja respondem por este e-mail (Username, Email ou Federation).

    Username e FederationIdentifier sao unicos; o Email nao, mas dois Users com o
    mesmo Email fazem `resolve_salesforce_identities` devolver `ambiguous` e
    congelam a pessoa para a automacao (mesma razao de `enable_partner_user`
    recusar `DUPLICATE_EMAIL`). Sobra de conversao NOSSA, ja aposentada, nao conta.
    """
    escaped = _esc_soql(wanted_email)
    result = sf.query(
        "SELECT Id, Username, Email, FederationIdentifier, IsActive FROM User "
        f"WHERE Username = '{escaped}' OR Email = '{escaped}' "
        f"OR FederationIdentifier = '{escaped}'"
    )
    return [
        record for record in (result.get('records') or [])
        if not field_contract.same_sf_id(record.get('Id'), user_id)
        and not _is_parked_leftover(record)
    ]


def _identity_readback(
    sf: Any, user_id: str, payload: Dict[str, str], before: Dict[str, Any]
) -> str:
    """Le o User de volta depois de um erro no DML da identidade.

    A identidade e UMA unidade: a leitura confere os TRES campos, nao so os que o
    DML enviou. Um campo que o plano nao enviou (ja estava alinhado) e que outro
    escritor mudou durante o timeout nao pode passar por sucesso.

    `landed`: os tres tem o valor esperado (o pedido, ou o que ja tinham). `unchanged`:
    os tres tem o valor que tinham ANTES. `other`: qualquer outro estado (parcial, ou
    um terceiro valor de outro escritor). `unknown`: a leitura falhou. So `landed` e
    `unchanged` sao afirmacoes; reler decide, repetir as cegas nao.
    """
    names = ('Username', 'Email', 'FederationIdentifier')
    try:
        result = sf.query(
            "SELECT Id, Username, Email, FederationIdentifier FROM User "
            f"WHERE Id = '{_validate_sf_id(user_id)}' LIMIT 1"
        )
        records = result.get('records') or []
        if not records:
            return 'unknown'
        stored = records[0]
        wanted = all(
            field_contract.same_value(name, stored.get(name), payload.get(name, before.get(name)))
            for name in names
        )
        previous = all(
            field_contract.same_value(name, stored.get(name), before.get(name))
            for name in names
        )
    except Exception:  # noqa: BLE001
        return 'unknown'
    if wanted:
        return 'landed'
    if previous:
        return 'unchanged'
    return 'other'


def get_salesforce_user_type(salesforce_user_id: Optional[str]) -> Optional[str]:
    """`UserType` do User no Salesforce, ou None se nao foi possivel ler.

    Serve a quem precisa distinguir Partner (vinculado a um Contact) de Standard
    (licenca interna, sem Contact por desenho) antes de cobrar o Contact ausente.
    """
    try:
        user_id = str(salesforce_user_id or '').strip()
        if not user_id or user_id == '0':
            return None
        sf = get_salesforce_connection()
        if not sf:
            return None
        found = sf.query(
            f"SELECT UserType FROM User WHERE Id = '{_validate_sf_id(user_id)}' LIMIT 1"
        )
        records = found.get('records') or []
        return (records[0].get('UserType') or None) if records else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("UserType do User nao lido: %s", field_contract.safe_error_text(exc))
        return None


def sync_salesforce_user_identity(
    salesforce_user_id: Optional[str],
    employee_data: Dict[str, Any],
    known_emails: Any = (),
    expected_contact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Faz Username, Email e FederationIdentifier do Partner User seguirem o e-mail.

    A decisao esta em `field_contract.plan_identity_sync`. `employee_data` precisa
    vir de `field_contract.with_identity` (carrega o e-mail ja decidido; sem ele a
    funcao recusa) e `known_emails` e o historico de e-mails do colaborador. Aqui
    entram so o I/O e as recusas que dependem do org: outro User ja usando o
    e-mail novo. Qualquer recusa e FAIL-CLOSED (nada e escrito) e sobe como
    `manual_required`: trocar o login de uma conta que alguem customizou, ou criar
    um par ambiguo, e pior do que deixar o e-mail antigo ate uma pessoa olhar.

    A identidade e UMA unidade: um unico DML, sem regravar campo a campo. Se o
    Salesforce recusar (ex.: `DUPLICATE_USERNAME` de outro org, que a consulta de
    colisao nao enxerga), nenhum dos tres campos muda; se a chamada falhar com
    resultado incerto (timeout), le o User de volta antes de afirmar qualquer coisa.

    Standard (licenca interna, gerida fora do MakersHub) nunca e tocado.
    """
    operation = "Sync Salesforce User Identity"
    base: Dict[str, Any] = {
        'success': True, 'executed': False, 'updated_fields': [],
        'skipped_fields': [], 'failed_fields': {},
    }
    try:
        user_id = str(salesforce_user_id or '').strip()
        if not user_id or user_id == '0':
            return {**base, 'success': False,
                    'message': 'User ID do Salesforce ausente; identidade não sincronizada'}
        sf = get_salesforce_connection()
        if not sf:
            notify_teams_salesforce_error(
                "Falha na autenticacao com o Salesforce", operation=operation
            )
            return {**base, 'success': False, 'executed': True,
                    'message': 'Falha na autenticação com o Salesforce'}
        found = sf.query(
            "SELECT Id, UserType, IsActive, ContactId, Username, Email, FederationIdentifier "
            f"FROM User WHERE Id = '{_validate_sf_id(user_id)}' LIMIT 1"
        )
        records = found.get('records') or []
        if not records:
            return {**base, 'success': False, 'executed': True,
                    'message': f'Usuário {user_id} não encontrado no Salesforce'}
        current = records[0]
        if (
            current.get('UserType') == field_contract.PARTNER_USER_TYPE
            and not field_contract.contact_ids_match(expected_contact_id, current.get('ContactId'))
        ):
            # O historico prova que o e-mail ja foi desta PESSOA, nao que este User e dela:
            # se o Id do Contact do cadastro aponta para outro Contact, o vinculo local
            # esta errado e trocar o login mexeria na conta de outra pessoa.
            return {**base, 'success': False, 'manual_required': True,
                    'error_code': 'IDENTITY_CONTACT_MISMATCH',
                    'message': (
                        'E-mail não sincronizado no Salesforce [IDENTITY_CONTACT_MISMATCH]: '
                        'o User pertence a outro Contact que o do cadastro; revisão manual'
                    )}
        desired = employee_data.get(field_contract.IDENTITY_KEY)
        plan = field_contract.plan_identity_sync(current, desired, known_emails)
        if plan.action in ('noop', 'skip_not_partner'):
            return {**base, 'message': f'Identidade do User: {plan.reason}'}
        if plan.action == 'refuse':
            return {**base, 'success': False, 'manual_required': True,
                    'error_code': plan.code,
                    'message': f'E-mail não sincronizado no Salesforce [{plan.code}]: {plan.reason}; revisão manual'}

        collisions = _identity_collisions(sf, user_id, str(desired))
        if collisions:
            ids = ', '.join(sorted(str(item.get('Id')) for item in collisions))
            return {**base, 'success': False, 'manual_required': True,
                    'error_code': 'IDENTITY_EMAIL_IN_USE',
                    'message': (
                        'E-mail não sincronizado no Salesforce [IDENTITY_EMAIL_IN_USE]: '
                        f'o e-mail novo já pertence a outro User ({ids}); revisão manual'
                    )}

        fields = sorted(plan.payload)
        try:
            sf.User.update(user_id, plan.payload)
        except Exception as update_error:  # noqa: BLE001
            code = _sync_failure_code(update_error)
            landed = _identity_readback(sf, user_id, plan.payload, current)
            if landed == 'landed':
                logger.warning(
                    "Identidade Salesforce do User %s: update falhou (%s) mas a leitura confirma o e-mail novo",
                    user_id, code,
                )
                return {**base, 'executed': True, 'updated_fields': fields,
                        'message': 'Identidade do User atualizada para o e-mail do cadastro '
                                   f"(confirmada por leitura após erro {code}): {', '.join(fields)}"}
            if landed == 'unchanged':
                outcome = (
                    'o Salesforce não aceitou a atualização da identidade (Username, Email e '
                    'FederationIdentifier ficaram como estavam)'
                )
            elif landed == 'other':
                outcome = (
                    'a leitura de volta não confirma nem o valor pedido nem o anterior de '
                    'Username, Email e FederationIdentifier (outro escritor, ou escrita parcial)'
                )
            else:
                outcome = (
                    'não foi possível confirmar quais valores de Username, Email e '
                    'FederationIdentifier ficaram no Salesforce'
                )
            message = f'E-mail não sincronizado no Salesforce [{code}]: {outcome}; revisão manual'
            notify_teams_salesforce_error(message, operation=operation)
            return {**base, 'success': False, 'executed': True, 'manual_required': True,
                    'error_code': code, 'failed_fields': {name: code for name in fields},
                    'message': message}
        logger.info(
            "Identidade Salesforce do User %s atualizada: campos=%s (Username %s -> %s)",
            user_id, fields,
            field_contract.mask_email(current.get('Username')),
            field_contract.mask_email(desired),
        )
        return {**base, 'executed': True, 'updated_fields': fields,
                'message': f"Identidade do User atualizada para o e-mail do cadastro: {', '.join(fields)}"}
    except Exception as exc:  # noqa: BLE001
        error_msg = f"Erro na sincronização da identidade do User: {field_contract.safe_error_text(exc)}"
        logger.error("❌ %s", error_msg)
        notify_teams_salesforce_error(error_msg, operation=operation)
        return {**base, 'success': False, 'executed': True, 'manual_required': True,
                'message': error_msg}


# ============================================================================
# R1 SCHEDULING FLOW — Salesforce Lead → Opportunity → Event
# ============================================================================

# Valid values for DWInteressesInvestimento__c (multi-select separated by ";")
VALID_INTERESSES_INVESTIMENTO = {
    "Renda fixa", "Renda variável", "Multimercado",
    "Exterior", "Fundo de investimentos",
}

VALID_INTERESSES_CONSORCIO = {
    "Imóvel", "Veículo", "Serviços",
}


def validate_lead_update_data(
    patrimony_value: float,
    profissao: str,
    interesse: str,
    description: str,
    is_consorcio: bool = False,
) -> List[str]:
    """Validate lead data before sending to Salesforce."""
    errors: List[str] = []

    if is_consorcio:
        # Consórcio: patrimony is informational, profissão not required
        if interesse and interesse.strip():
            valores = [v.strip() for v in interesse.split(";")]
            invalidos = [v for v in valores if v not in VALID_INTERESSES_CONSORCIO]
            if invalidos:
                errors.append(
                    f"Interesses consórcio inválidos: {invalidos}. "
                    f"Válidos: {sorted(VALID_INTERESSES_CONSORCIO)}"
                )
    else:
        if not patrimony_value or patrimony_value <= 0:
            errors.append("Patrimônio é obrigatório e deve ser maior que zero")

        if not profissao or not profissao.strip():
            errors.append("Profissão é obrigatória")

        if not interesse or not interesse.strip():
            errors.append("Interesse em investimentos é obrigatório")
        else:
            valores = [v.strip() for v in interesse.split(";")]
            invalidos = [v for v in valores if v not in VALID_INTERESSES_INVESTIMENTO]
            if invalidos:
                errors.append(
                    f"Interesses inválidos: {invalidos}. "
                    f"Válidos: {sorted(VALID_INTERESSES_INVESTIMENTO)}"
                )

    if not description or not description.strip():
        errors.append("Descrição é obrigatória (mínimo 200 caracteres no Salesforce)")

    return errors


def update_lead_fields(
    sf: Salesforce,
    lead_id: str,
    patrimony_value: float,
    patrimony_range: str,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    # Consórcio-specific fields (all optional, null for standard leads)
    is_consorcio: bool = False,
    idade: Optional[int] = None,
    modalidade_calculo: Optional[str] = None,
    id_carta: Optional[int] = None,
    tomador_decisao: Optional[str] = None,
    intuito_consorcio: Optional[str] = None,
    interesses_consorcios: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update Lead fields before conversion.

    For standard (Faz Capital) leads:
    - DWPatrimonioFinanceiroInformado__c, FaixadePLInformada__c
    - DWProfissao__c, DWInteressesInvestimento__c, Description

    For Consórcio leads:
    - Idade__c, ModalidadeCalculo__c, IdCarta__c
    - TomadorDecisao__c, IntuitoConsorcio__c, InteressesConsorcios__c
    - Description
    """
    if is_consorcio:
        update_data: Dict[str, Any] = {
            "Idade__c": idade,
            "ModalidadeCalculo__c": modalidade_calculo,
            "IdCarta__c": id_carta,
            "TomadorDecisao__c": tomador_decisao,
            "IntuitoConsorcio__c": intuito_consorcio,
            "InteressesConsorcios__c": interesses_consorcios,
            "Description": description or "",
            "DWPatrimonioFinanceiroInformado__c": patrimony_value,
            "DWValorLead__c": patrimony_value,
            "FaixadePLInformada__c": patrimony_range,
        }
    else:
        update_data = {
            "DWPatrimonioFinanceiroInformado__c": patrimony_value,
            "DWValorLead__c": patrimony_value,  # "Valor para investir" — required for conversion
            "FaixadePLInformada__c": patrimony_range,
            "DWProfissao__c": profissao,
            "DWInteressesInvestimento__c": interesse_investimentos,
            "Description": description or "",
        }
    update_data = {k: v for k, v in update_data.items() if v is not None}

    try:
        sf.Lead.update(lead_id, update_data)  # type: ignore
        logger.info("Lead %s updated: %s", lead_id, list(update_data.keys()))
        return {"success": True, "message": "Lead atualizado com sucesso"}
    except Exception as e:
        logger.error("Error updating Lead %s: %s", lead_id, e)
        return {"success": False, "message": str(e)}


def _get_converted_lead_status(sf: Salesforce) -> str:
    """
    Query the org's LeadStatus to find the converted status label.
    Caches result for the session lifetime.
    """
    result = sf.query(
        "SELECT Id, MasterLabel FROM LeadStatus WHERE IsConverted = true LIMIT 1"
    )
    if result.get("totalSize", 0) == 0:
        raise ValueError("No converted LeadStatus found in org — check Salesforce setup")
    return result["records"][0]["MasterLabel"]


def _build_convert_lead_soap_envelope(
    session_id: str,
    lead_id: str,
    converted_status: str,
    owner_id: Optional[str] = None,
    opportunity_name: Optional[str] = None,
    do_not_create_opportunity: bool = False,
    send_notification_email: bool = False,
) -> str:
    """Build the SOAP XML envelope for the convertLead() call."""
    # XML-escape every interpolated value at the sink: opportunity_name is
    # mounted from the Lead's own Name/LeadSource (attacker-influenced via the
    # org's lead intake), so a value containing '</urn:opportunityName>' could
    # otherwise inject convertLead elements (e.g. ownerId). For well-formed
    # values (SF Ids, session ids, statuses) escaping is a no-op.
    safe_session_id = _xml_escape(session_id or "")
    safe_lead_id = _xml_escape(lead_id or "")
    safe_converted_status = _xml_escape(converted_status or "")
    safe_owner_id = _xml_escape(owner_id or "")
    safe_opportunity_name = _xml_escape(opportunity_name or "")
    # Optional elements
    owner_xml = f"<urn:ownerId>{safe_owner_id}</urn:ownerId>" if owner_id else ""
    opp_name_xml = (
        f"<urn:opportunityName>{safe_opportunity_name}</urn:opportunityName>"
        if opportunity_name and not do_not_create_opportunity
        else ""
    )
    do_not_create_xml = (
        f"<urn:doNotCreateOpportunity>true</urn:doNotCreateOpportunity>"
        if do_not_create_opportunity
        else "<urn:doNotCreateOpportunity>false</urn:doNotCreateOpportunity>"
    )
    send_email_xml = (
        f"<urn:sendNotificationEmail>true</urn:sendNotificationEmail>"
        if send_notification_email
        else ""
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:urn="urn:partner.soap.sforce.com">
    <soapenv:Header>
        <urn:SessionHeader>
            <urn:sessionId>{safe_session_id}</urn:sessionId>
        </urn:SessionHeader>
    </soapenv:Header>
    <soapenv:Body>
        <urn:convertLead>
            <urn:leadConverts>
                <urn:leadId>{safe_lead_id}</urn:leadId>
                <urn:convertedStatus>{safe_converted_status}</urn:convertedStatus>
                {owner_xml}
                {opp_name_xml}
                {do_not_create_xml}
                {send_email_xml}
            </urn:leadConverts>
        </urn:convertLead>
    </soapenv:Body>
</soapenv:Envelope>"""


def _parse_convert_lead_response(response_text: str) -> Dict[str, Any]:
    """Parse the SOAP XML response from convertLead()."""
    root = SafeET.fromstring(response_text)

    # Namespace map for parsing
    ns = {
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "sf": "urn:partner.soap.sforce.com",
    }

    # Check for SOAP Fault first
    fault = root.find(".//soapenv:Body/soapenv:Fault", ns)
    if fault is not None:
        fault_string = fault.findtext("faultstring", "Unknown SOAP fault")
        return {"success": False, "message": f"SOAP Fault: {fault_string}"}

    # Find the convertLeadResponse / result element
    # The response structure is: Body > convertLeadResponse > result
    result_elem = root.find(".//sf:convertLeadResponse/sf:result", ns)
    if result_elem is None:
        # Try without namespace prefix (some versions differ)
        result_elem = root.find(".//{urn:partner.soap.sforce.com}result")

    if result_elem is None:
        return {"success": False, "message": "Could not parse convertLead response"}

    def find_text(tag: str) -> Optional[str]:
        elem = result_elem.find(f"sf:{tag}", ns)
        if elem is None:
            elem = result_elem.find(f"{{urn:partner.soap.sforce.com}}{tag}")
        return elem.text if elem is not None else None

    success = find_text("success")
    if success and success.lower() == "true":
        return {
            "success": True,
            "account_id": find_text("accountId"),
            "contact_id": find_text("contactId"),
            "opportunity_id": find_text("opportunityId"),
        }

    # Extract errors
    errors_elem = result_elem.find("sf:errors", ns)
    if errors_elem is None:
        errors_elem = result_elem.find("{urn:partner.soap.sforce.com}errors")
    error_msg = "Conversion failed"
    if errors_elem is not None:
        msg = errors_elem.findtext(
            "sf:message", None, ns
        ) or errors_elem.findtext(
            "{urn:partner.soap.sforce.com}message"
        )
        if msg:
            error_msg = msg

    return {"success": False, "message": error_msg}


def convert_lead_to_opportunity(
    sf: Salesforce,
    lead_id: str,
    sdr_user_id: str,
    lead_name: str,
    lead_source: Optional[str] = None,
    create_opportunity: bool = True,
) -> Dict[str, Any]:
    """
    Convert a Lead to Opportunity via Salesforce SOAP API convertLead().

    Uses the native SOAP API (no custom Apex required). The REST API does
    NOT support lead conversion, but we can POST a SOAP envelope directly
    using the session_id from our existing simple_salesforce connection.

    Args:
        sf: Authenticated Salesforce connection.
        lead_id: Lead ID (00Q...).
        sdr_user_id: Salesforce User ID of the SDR (005...) — becomes the owner.
        lead_name: Lead name for the Opportunity name.
        lead_source: Lead source / campaign (e.g. "CONEXAO25") for the Opportunity name.
        create_opportunity: Whether to create an Opportunity (default True).

    Returns:
        dict with success, opportunity_id, contact_id, account_id.
    """
    try:
        # 1. Get the org's converted lead status
        converted_status = _get_converted_lead_status(sf)
        logger.info("Using converted status: '%s'", converted_status)

        # 2. Build SOAP envelope
        # Opportunity name format: "{lead_name} - {campaign}" or "{lead_name}" if no campaign
        opp_name = f"{lead_name} - {lead_source}" if lead_source else lead_name
        soap_body = _build_convert_lead_soap_envelope(
            session_id=sf.session_id,
            lead_id=lead_id,
            converted_status=converted_status,
            owner_id=sdr_user_id,
            opportunity_name=opp_name,
            do_not_create_opportunity=not create_opportunity,
        )

        # 3. POST to SOAP Partner endpoint
        soap_url = f"https://{sf.sf_instance}/services/Soap/u/{sf.sf_version}"
        headers = {
            "Content-Type": "text/xml; charset=UTF-8",
            "SOAPAction": "convertLead",
        }
        response = requests.post(
            soap_url,
            data=soap_body.encode("utf-8"),
            headers=headers,
            timeout=30,
        )

        if response.status_code not in (200, 500):
            # 500 may contain SOAP faults which we parse below
            logger.error(
                "SOAP convertLead HTTP %s: %s",
                response.status_code,
                response.text[:500],
            )
            return {
                "success": False,
                "message": f"HTTP {response.status_code} from Salesforce SOAP API",
            }

        # 4. Parse response
        result = _parse_convert_lead_response(response.text)

        if result.get("success"):
            logger.info(
                "Lead %s converted via SOAP. Opp: %s, Contact: %s, Account: %s",
                lead_id,
                result.get("opportunity_id"),
                result.get("contact_id"),
                result.get("account_id"),
            )
        else:
            logger.error("Failed to convert Lead %s: %s", lead_id, result.get("message"))

        return result

    except Exception as e:
        logger.error("Error converting Lead %s: %s", lead_id, e, exc_info=True)
        return {"success": False, "message": str(e)}


def update_ownership_after_conversion(
    sf: Salesforce,
    account_id: Optional[str],
    contact_id: Optional[str],
    advisor_salesforce_id: str,
    advisor_name: str,
) -> Dict[str, Any]:
    """
    Transfer Account and Contact ownership to the advisor after lead conversion.

    During conversion, Salesforce sets the owner of the new Account/Contact to
    the SDR (the user who triggered the conversion). The advisor must be the
    owner so that the records appear in the advisor's Salesforce views and the
    client sees the advisor's name on emails/notifications.
    """
    results: Dict[str, Any] = {"success": True, "updated": []}

    # Update Account owner
    if account_id:
        try:
            sf.Account.update(account_id, {"OwnerId": advisor_salesforce_id})  # type: ignore
            logger.info(
                "Account %s OwnerId updated → %s (%s)",
                account_id, advisor_salesforce_id, advisor_name,
            )
            results["updated"].append("account")
        except Exception as e:
            logger.error("Error updating Account %s owner: %s", account_id, e)
            results["account_error"] = str(e)
            results["success"] = False

    # Update Contact owner
    if contact_id:
        try:
            sf.Contact.update(contact_id, {"OwnerId": advisor_salesforce_id})  # type: ignore
            logger.info(
                "Contact %s OwnerId updated → %s (%s)",
                contact_id, advisor_salesforce_id, advisor_name,
            )
            results["updated"].append("contact")
        except Exception as e:
            logger.error("Error updating Contact %s owner: %s", contact_id, e)
            results["contact_error"] = str(e)
            results["success"] = False

    return results


def account_has_consorcio_origin(sf: Salesforce, account_id: str) -> bool:
    """
    True when the Account was converted from a Consórcios Lead.

    Accounts carry no consórcio RecordType of their own, so the converting
    Lead's RecordType is the source of truth for consórcio routing on every
    Account→Opportunity path (FBI-2386). EXISTS semantics: any converted
    Consórcios Lead counts, so an Account with mixed conversion history keeps
    its consórcio origin. `account_id` must already be SF-id-validated by the
    caller. Best-effort: a query failure logs and degrades to False (fail-open
    to the caller's explicit intent) rather than blocking scheduling.
    """
    soql = (
        "SELECT Id FROM Lead "
        f"WHERE ConvertedAccountId = '{account_id}' AND IsConverted = true "
        "AND RecordType.DeveloperName = 'Consorcios' LIMIT 1"
    )
    try:
        res = sf.query(soql)
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "consórcio-origin lookup failed for Account %s (%s); "
            "falling back to caller intent — may misclassify as investimentos",
            account_id, e,
        )
        return False
    return bool(res.get("records"))


# Name fallback (UI label) for the Opportunity RecordType lookup, e.g.
# "Financial Services". Module-level so a test can pin the escape at the sink
# without reaching into a function-local literal.
_OPP_RT_NAME_FALLBACKS: dict[str, tuple[str, ...]] = {
    "investimentos": ("Investimentos",),
    "financial_services": ("Financial Services",),
}


def _resolve_opportunity_record_type_id(sf: Salesforce, funnel: str) -> Optional[str]:
    """
    Resolve Opportunity RecordType Id for an Investimentos funnel via SOQL
    (same pattern as Consórcios). Tries DeveloperName candidates, then Name.
    """
    from app.services.super_r1_service import OPP_RT_SOQL_CANDIDATES

    candidates = OPP_RT_SOQL_CANDIDATES.get(funnel) or ()
    for dev_name in candidates:
        try:
            rt_result = sf.query(
                "SELECT Id FROM RecordType "
                f"WHERE SobjectType = 'Opportunity' AND IsActive = true "
                f"AND DeveloperName = '{dev_name}' LIMIT 1"
            )
            if rt_result.get("totalSize", 0) > 0:
                return rt_result["records"][0]["Id"]
        except Exception as e:  # noqa: BLE001
            logger.warning("Opp RT SOQL by DeveloperName=%s failed: %s", dev_name, e)

    for name in _OPP_RT_NAME_FALLBACKS.get(funnel, ()):
        try:
            # SOQL escape (`\'`), not the SQL idiom of doubling the quote: the
            # sink must speak one dialect only, or a future non-literal value
            # would leave the literal unclosed.
            safe_name = _esc_soql(name)
            rt_result = sf.query(
                "SELECT Id FROM RecordType "
                f"WHERE SobjectType = 'Opportunity' AND IsActive = true "
                f"AND Name = '{safe_name}' LIMIT 1"
            )
            if rt_result.get("totalSize", 0) > 0:
                return rt_result["records"][0]["Id"]
        except Exception as e:  # noqa: BLE001
            logger.warning("Opp RT SOQL by Name=%s failed: %s", name, e)

    logger.warning(
        "Could not resolve Opportunity RecordType for funnel=%s "
        "(tried DeveloperNames=%s). Provide the correct DeveloperName if this persists.",
        funnel,
        candidates,
    )
    return None


@dataclass(frozen=True)
class ReusedOpportunityState:
    """Fase, prazo e status de reunião da OPP de entrada antes da R1 (FBI-4719).

    Campos como vêm do Salesforce (StageName, CloseDate em ISO,
    DWStatusReunioesInvestimentos__c). None é desconhecido.
    """

    stage: Optional[str] = None
    close_date: Optional[str] = None
    meeting_status: Optional[str] = None
    # RecordType.DeveloperName da OPP quando a requisição começou. Fora da comparação:
    # a releitura não o traz; ele só diz qual regra do Flow da org se aplica a ela.
    record_type: Optional[str] = field(default=None, compare=False)


# FBI-4719: o que a R1 do Super R1 faz avançar numa OPP reaproveitada. A OPP
# que já passou disso mantém a fase e o status de reunião (review do PR #594):
# em Contatado (Apresentação da Estratégia, em consórcio) ou além, ou com R1
# realizada, R2 ou R3.
_STAGES_BEFORE_R1 = frozenset({"Nova oportunidade", "Qualificação"})
_MEETING_STATUSES_BEFORE_R1 = frozenset(
    {"", "R1 Não agendada", "R1 Agendada em aberto", "R1 Agendada e não realizada"}
)


_SP_TZ = ZoneInfo("America/Sao_Paulo")

# Salesforce Flow `DWCompromissoAfterCreateAtualizaFaseOportunidadeComR1Marcada`
# (fires for an Event of Type R1 on an Opportunity, unless the last modifier is one
# excluded user): creating the R1 Event moves an Opportunity still in this stage
# forward, by its RecordType as it is when the Event is created: Investimentos and
# FinancialServices → Contatado; Consorcios, Seguros and Internacional → Apresentação
# da Estratégia (live org, Flow version 6, read through the Tooling API). It is
# the one change to the reused OPP that the booking itself causes.
_STAGE_ADVANCED_BY_THE_R1_EVENT = "Nova oportunidade"
_STAGE_SET_BY_THE_R1_EVENT_BY_RECORD_TYPE = {
    "Investimentos": "Contatado",
    "FinancialServices": "Contatado",
    "Consorcios": "Apresentação da Estratégia",
    "Seguros": "Apresentação da Estratégia",
    "Internacional": "Apresentação da Estratégia",
}


def _is_the_r1_event_advancing_the_stage(
    snapshot: ReusedOpportunityState, fresh: ReusedOpportunityState,
) -> bool:
    """True when the Flow of the org explains the change: "Nova oportunidade" turned
    into exactly the stage the Flow sets for the RecordType the Opportunity had, with
    nothing else different. A RecordType the Flow has no rule for (Family Office, for
    example, or none at all), another stage, or any other field changed is not this. A person who
    moves it to that very stage within the seconds of the booking cannot be told apart
    (accepted, ADR 0095)."""
    expected = _STAGE_SET_BY_THE_R1_EVENT_BY_RECORD_TYPE.get(snapshot.record_type or "")
    return (
        snapshot.stage == _STAGE_ADVANCED_BY_THE_R1_EVENT
        and expected is not None
        and fresh.stage == expected
        and fresh.close_date == snapshot.close_date
        and fresh.meeting_status == snapshot.meeting_status
    )


def _today_brt() -> date:
    """Today on the Brasília calendar. `date.today()` is the day in the PROCESS time
    zone: in a UTC container, between 21:00 and 24:00 in Brasília it is already the
    next day."""
    return datetime.now(_SP_TZ).date()


def _is_past_date(iso_date: Optional[str]) -> bool:
    """Prazo ISO já vencido. Ausente ou ilegível conta como desconhecido (False)."""
    try:
        return iso_date is not None and date.fromisoformat(iso_date) < _today_brt()
    except ValueError:
        logger.warning("CloseDate ilegível na OPP reaproveitada: %r", iso_date)
        return False


def _fresh_reused_opportunity_state(
    sf: Salesforce, opportunity_id: str, snapshot: Optional[ReusedOpportunityState],
) -> Optional[ReusedOpportunityState]:
    """Stage, close date and meeting status of a reused OPP, read right now; None
    when they cannot be confirmed.

    `snapshot` was read when the request started; the PATCH that decides whether
    stage and meeting status advance runs after the Account, Contact and Event
    writes, seconds later. Anyone editing the OPP in Salesforce in between would
    be overwritten by a decision made on stale state, so the decision is taken on
    a re-read made immediately before the PATCH. The window that remains is the
    round trip between this read and the PATCH.

    A stage change that the Flow of the org explains (see
    `_is_the_r1_event_advancing_the_stage`) is taken as the booking's own effect and
    not as an edit by someone: it is decided on the state the SDR saw (`snapshot`).
    Deciding on the re-read would leave a consórcio booking of an Investimentos
    Opportunity in "Contatado", because the Flow runs before this flow switches the
    RecordType; the update writes the stage it means.

    A failed or empty read returns None, and the caller then decides NOTHING
    that depends on the state (see `stage_state_unknown` in
    `update_opportunity_after_conversion`) and reports a partial step, so the
    booking that is already made never fails and a re-submission completes it.
    Falling back to `snapshot` would be the unsafe guess: it is exactly the state
    that may have gone stale.

    `If-Unmodified-Since` on the PATCH is not used: it can only protect writes
    that come after the precondition, and the Event created by this same flow can
    touch the OPP, which would refuse the PATCH after the booking is already made.
    """
    try:
        validated = _validate_sf_id(opportunity_id)
        records = sf.query(  # type: ignore[attr-defined]
            "SELECT StageName, CloseDate, DWStatusReunioesInvestimentos__c "
            f"FROM Opportunity WHERE Id = '{validated}' AND IsDeleted = false"
        ).get("records") or []
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Could not re-read reused opportunity %s before the update; stage, "
            "meeting status and close date are left as they are: %s",
            opportunity_id, exc,
        )
        return None
    if not records:
        logger.warning(
            "Reused opportunity %s not found on re-read; stage, meeting status and "
            "close date are left as they are", opportunity_id,
        )
        return None
    record = records[0]
    fresh = ReusedOpportunityState(
        stage=record.get("StageName"),
        close_date=record.get("CloseDate"),
        meeting_status=record.get("DWStatusReunioesInvestimentos__c"),
    )
    if snapshot is not None and fresh != snapshot:
        if _is_the_r1_event_advancing_the_stage(snapshot, fresh):
            logger.info(
                "Reused opportunity %s moved as the R1 Event Flow would move it (%s -> %s); "
                "the update decides on the state the SDR saw",
                opportunity_id, snapshot.stage, fresh.stage,
            )
            return snapshot
        logger.warning(
            "Reused opportunity %s changed in Salesforce while the booking ran "
            "(%s -> %s); the update decides on the fresh state",
            opportunity_id, snapshot, fresh,
        )
    return fresh


def _advance_fields(
    state: Optional[ReusedOpportunityState], *, is_consorcio: bool,
) -> Dict[str, Any]:
    """Stage and meeting status the R1 moves forward, each decided on its own.

    `state` None is a new Opportunity (everything moves). A reused one moves only
    what is still before the R1: a stage the Flow of the org already advanced is
    left alone and the meeting status is still written."""
    fields: Dict[str, Any] = {}
    if state is None or state.stage is None or state.stage in _STAGES_BEFORE_R1:
        fields["StageName"] = "Apresentação da Estratégia" if is_consorcio else "Contatado"
    if state is None or (state.meeting_status or "") in _MEETING_STATUSES_BEFORE_R1:
        fields["DWStatusReunioesInvestimentos__c"] = "R1 Agendada em aberto"
    return fields


def _renew_expired_close_date_fields(
    state: Optional[ReusedOpportunityState],
) -> Dict[str, Any]:
    """The close date an open reused Opportunity gets when its own has passed.

    A lost Opportunity never gets here (`opportunity_entry_refusal`). An open one
    whose deadline already passed gets the close date of a new one (today in
    Brasília + 90 days, as `execute_r1_from_opportunity_flow` gives the
    Opportunity it creates); one still within its deadline keeps its own."""
    if state is not None and _is_past_date(state.close_date):
        return {"CloseDate": (_today_brt() + timedelta(days=90)).isoformat()}
    return {}


def update_opportunity_after_conversion(
    sf: Salesforce,
    opportunity_id: str,
    advisor_salesforce_id: str,
    advisor_name: str,
    sdr_name: str,
    patrimony_value: float,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    is_consorcio: bool = False,
    reused_opportunity: bool = False,
    current_state: Optional[ReusedOpportunityState] = None,
    stage_state_unknown: bool = False,
) -> Dict[str, Any]:
    """
    Update the newly-created Opportunity with routing & lead data.

    `reused_opportunity` (FBI-4719, entrada por OPP existente): a descrição é do
    assessor e guarda o histórico da OPP, então fica como está. Os
    demais campos são a requalificação que o SDR acabou de fazer e sobrescrevem.
    `current_state` é a OPP antes da R1. Fase e status de reunião só avançam
    (_STAGES_BEFORE_R1, _MEETING_STATUSES_BEFORE_R1), e o prazo é renovado
    quando o da OPP aberta já venceu (a perdida nunca chega aqui:
    `opportunity_entry_refusal`). `current_state=None` (sem leitura
    do inicio) avança, como numa OPP nova; já `stage_state_unknown=True` (a
    releitura imediatamente antes falhou) não decide nada disso.

    `stage_state_unknown` (reused only): the state could not be re-read right
    before this update, so nothing that depends on it is decided here. Stage,
    meeting status and close date stay as they are in Salesforce: guessing from
    a stale snapshot could send back an Opportunity that someone moved forward. Owner, patrimony and the SDR fields still go.

    Confirmed fields (from salesforce_prod.stg_salesforce__opportunity):
    - OwnerId                              → Advisor
    - StageName                            → 'Contatado' (one step past default)
    - DWStatusReunioesInvestimentos__c      → 'R1 Agendada em aberto'
    - DWPatrimonioFinanceiroInformado__c    → patrimony
    - DWProfissao__c                        → profession
    - DWInteressesInvestimento__c           → investment interests
    - DWValorInformadoPeloSDR__c            → SDR-informed value
    - DWNomeSDR__c                          → SDR name
    - DWDescricaoOportunidade__c            → "" (empty — advisor fills later)
    Note: DWNomeAssessor__c is a formula field (read-only) — do NOT include it.
    """
    state = current_state if reused_opportunity else None
    update_data: Dict[str, Any] = {
        "OwnerId": advisor_salesforce_id,
        "DWPatrimonioFinanceiroInformado__c": patrimony_value,
        "DWValorInformadoPeloSDR__c": patrimony_value,
        "DWNomeSDR__c": sdr_name,
    }
    hold_state = reused_opportunity and stage_state_unknown
    if not hold_state:
        update_data.update(_advance_fields(state, is_consorcio=is_consorcio))
    if not reused_opportunity:
        update_data["DWDescricaoOportunidade__c"] = ""

    if not is_consorcio:
        update_data["DWProfissao__c"] = profissao
        update_data["DWInteressesInvestimento__c"] = interesse_investimentos

    # Set Consórcios-specific fields
    if is_consorcio:
        update_data["DWEspecialistaResponsavel__c"] = advisor_salesforce_id

    # Set Consórcios RecordType on the Opportunity
    if is_consorcio:
        try:
            rt_result = sf.query(
                "SELECT Id FROM RecordType "
                "WHERE SobjectType = 'Opportunity' AND DeveloperName = 'Consorcios' AND IsActive = true LIMIT 1"
            )
            if rt_result.get("totalSize", 0) > 0:
                update_data["RecordTypeId"] = rt_result["records"][0]["Id"]
                logger.info("Setting Opportunity RecordType to Consórcios: %s", update_data["RecordTypeId"])
        except Exception as e:
            logger.warning("Could not resolve Consórcios RecordType for Opportunity: %s", e)
    else:
        # FBI-2925: Investimentos (<300k) vs Financial Services (≥300k) via SOQL
        try:
            from app.services.super_r1_service import (
                opportunity_funnel,
                patrimony_to_categoria,
            )
            funnel = opportunity_funnel(patrimony_to_categoria(patrimony_value))
            rt_id = _resolve_opportunity_record_type_id(sf, funnel) if funnel else None
            if rt_id:
                update_data["RecordTypeId"] = rt_id
                logger.info(
                    "Setting Opportunity RecordType funnel=%s id=%s (patrimony=%s)",
                    funnel,
                    rt_id,
                    patrimony_value,
                )
        except Exception as e:
            logger.warning("Could not resolve Investimentos/FS RecordType for Opportunity: %s", e)
    update_data = {k: v for k, v in update_data.items() if v is not None}

    if reused_opportunity and not hold_state:
        # OPP aberta com o prazo vencido ganha o prazo da OPP nova do caminho Conta
        # (execute_r1_from_opportunity_flow). A perdida não entra (recusa na entrada).
        update_data.update(_renew_expired_close_date_fields(state))

    try:
        sf.Opportunity.update(opportunity_id, update_data)  # type: ignore
        logger.info(
            "Opportunity %s updated: owner=%s, stage=Contatado",
            opportunity_id, advisor_salesforce_id,
        )
        return {"success": True, "message": "Opportunity atualizada com sucesso"}
    except Exception as e:
        logger.error("Error updating Opportunity %s: %s", opportunity_id, e)
        return {"success": False, "message": str(e)}


# Client-facing R1 calendar-invite body written to DescricaoInviteVisivelPeloCliente__c
# (Salesforce Text 255). CROSS-REPO CONTRACT (FBI-2324): must stay byte-identical to
# airflow-dags toolkit/super_r1_d1_utils/batch.py::R1_EVENT_EXTERNAL_DESCRIPTION — the
# D+1 batch and this real-time path create the SAME R1 Event; divergence between the two
# is the bug this contract guards. Pinned by tests/unit/test_r1_event_schema.py.
R1_EVENT_EXTERNAL_DESCRIPTION = (
    "Olá, aqui está o link para sua reunião com o especialista. "
    "Obrigado pela confiança!"
)


# `DWStatusReuniao__c` of an R1 whose meeting is still to happen. "Não realizada" is
# the cancelled one (it frees the slot and the Opportunity) and "Concluída" the held
# one. One owner: the Event is created with it, and the dedupe of a retry and the
# Super R1 lookups of an existing R1 (`qualify_service`) filter by it.
R1_EVENT_OPEN_STATUS = "Aberta"


def _format_salesforce_datetime(value: datetime) -> str:
    """Serialize an aware datetime with its offset and preserve the naive legacy."""
    if value.utcoffset() is None:
        return value.strftime("%Y-%m-%dT%H:%M:%S.000-03:00")
    return value.isoformat(timespec="milliseconds")


def create_r1_event(
    sf: Salesforce,
    opportunity_id: str,
    contact_id: Optional[str],
    advisor_salesforce_id: str,
    event_datetime: datetime,
    description: str,
    duration_minutes: int = MEETING_DURATION,
    modalidade: str = "Online",
) -> Dict[str, Any]:
    """
    Create an R1 Event in Salesforce linked to the Opportunity.

    Confirmed from sandbox Event schema:
    - Subject: picklist → "R1 Cliente", "R2 Cliente", "R3 Cliente", "Other"
    - Type: picklist → "R1", "R2", "Relacionamento", "Alocação", "Outros"
    - DWStatusReuniao__c: picklist → "Aberta", "Concluída", "Não realizada"
    - DWModalidade__c: picklist → "Online", "Presencial"
    - DWSincronizarOutlook__c: boolean (not string!)
    - ShowAs: picklist → "Busy", "OutOfOffice", "Free"
    - DurationInMinutes: int
    """
    # Soma em tempo REAL, nao em relogio de parede: com `event_datetime` aware,
    # `+ timedelta` preserva o offset de origem e o intervalo serializado deixa
    # de bater com `DurationInMinutes` quando a reuniao cruza uma virada de
    # horario de verao (FBI-3503). `StartDateTime` nao muda.
    end_datetime = add_real_minutes(event_datetime, duration_minutes)

    start_str = _format_salesforce_datetime(event_datetime)
    end_str = _format_salesforce_datetime(end_datetime)

    # Description (Long Text 32000, label "Comentários") = INTERNAL SDR notes from Super R1
    # DescricaoInviteVisivelPeloCliente__c (Text 255) = EXTERNAL — goes in the client calendar invite
    invite_visible_description = R1_EVENT_EXTERNAL_DESCRIPTION[:255]

    comments = (description or "").strip()

    # Advisor-facing calendar title. DIVERGES from the D+1 batch on purpose while only
    # this repo ships: airflow-dags toolkit/super_r1_d1_utils/batch.py::R1_EVENT_SUBJECT
    # still writes "Faz Capital - Institucional". Aligning both is a separate wave.
    # Pinned by tests/unit/test_r1_event_schema.py.
    event_data: Dict[str, Any] = {
        "Subject": "Reunião | Faz Capital",
        "Type": "R1",
        "DWStatusReuniao__c": R1_EVENT_OPEN_STATUS,
        "DWModalidade__c": modalidade,
        "DWSincronizarOutlook__c": True,
        "ShowAs": "Busy",
        "StartDateTime": start_str,
        "EndDateTime": end_str,
        "DurationInMinutes": duration_minutes,
        "WhatId": opportunity_id,
        "OwnerId": advisor_salesforce_id,
        "Description": comments,
        "DescricaoInviteVisivelPeloCliente__c": invite_visible_description,
    }

    if contact_id:
        event_data["WhoId"] = contact_id

    try:
        # A converted Lead cannot be converted again. Retrying its post-conversion
        # phase must therefore reuse an R1 already created before a later step
        # failed, instead of duplicating the calendar appointment. Only an OPEN R1
        # counts: a cancelled one ("Não realizada") does not hold the slot.
        existing = sf.query(
            "SELECT Id FROM Event "
            f"WHERE WhatId = '{_validate_sf_id(opportunity_id)}' "
            "AND Type = 'R1' "
            f"AND DWStatusReuniao__c = '{R1_EVENT_OPEN_STATUS}' "
            f"AND OwnerId = '{_validate_sf_id(advisor_salesforce_id)}' "
            f"AND StartDateTime = {start_str} "
            "ORDER BY CreatedDate DESC LIMIT 1"
        )
        if existing.get("totalSize", 0) > 0:
            event_id = existing["records"][0]["Id"]
            logger.info("R1 Event already exists for retry: %s", event_id)
            return {"success": True, "event_id": event_id, "message": "Evento R1 já existente"}

        result = sf.Event.create(event_data)  # type: ignore

        if result.get("success"):
            event_id = str(result.get("id") or "").strip()
            if not event_id:
                logger.error(
                    "Salesforce reported Event success without a durable id for Opp %s",
                    opportunity_id,
                )
                return {
                    "success": False,
                    "event_write_outcome": "write_started_unknown",
                    "message": "Salesforce confirmou o write sem retornar Event id",
                }
            logger.info(
                "R1 Event created: %s | Opp: %s | Advisor: %s | %s | %dmin",
                event_id, opportunity_id, advisor_salesforce_id,
                start_str, duration_minutes,
            )
            return {
                "success": True,
                "event_id": event_id,
                "event_write_outcome": "event_created",
                "message": "Evento R1 criado com sucesso",
            }

        errors = result.get("errors", [])
        error_msg = "; ".join(str(e) for e in errors) if errors else "Erro desconhecido"
        logger.error("Failed to create R1 Event: %s", error_msg)
        return {
            "success": False,
            "event_write_outcome": "event_not_created",
            "message": error_msg,
        }

    except Exception as e:
        logger.error("Error creating R1 Event for Opp %s: %s", opportunity_id, e)
        return {
            "success": False,
            "event_write_outcome": "write_started_unknown",
            "message": str(e),
        }


async def get_advisor_salesforce_id(
    session: AsyncSession,
    employee_id: int,
    advisor_name: Optional[str] = None,
    sf: Optional[Salesforce] = None,
) -> Optional[str]:
    """
    Look up the Salesforce User ID for an advisor from dim_advisor_scd2.salesforce_user_id.

    This is the canonical source — the same field used by call_list_repo,
    insurance_repo, and routing_repo throughout the system.  Salesforce
    preserves User IDs across sandbox refreshes, so these IDs work in both
    production and sandbox without any special handling.
    """
    query = text("""
        SELECT salesforce_user_id
        FROM makershub.dim_advisor_scd2
        WHERE employee_id = :employee_id
          AND is_active = true
          AND is_current = true
    """)
    result = await session.execute(query, {"employee_id": employee_id})
    row = result.fetchone()

    if row and row.salesforce_user_id:
        logger.info(
            "Advisor %s (%s) SF ID resolved: %s",
            employee_id, advisor_name or "?", row.salesforce_user_id,
        )
        return str(row.salesforce_user_id)

    logger.error(
        "sf_user_id not found in dim_advisor_scd2 for advisor %s (%s) — "
        "this is a data quality issue that must be fixed at the source",
        employee_id, advisor_name,
    )
    return None


_sync_engine = None


def _get_sync_engine():
    """Singleton sync engine for use in synchronous executor contexts."""
    global _sync_engine
    if _sync_engine is None:
        from app.core.config import GetSettings
        settings = GetSettings()
        connection_url = URL.create(
            "postgresql+psycopg2",
            username=settings.dbUser,
            password=settings.dbPass,
            host=settings.dbHost,
            port=settings.dbPort,
            database=settings.dbName,
        )
        engine_kwargs = {
            "pool_pre_ping": True,
            "connect_args": {"application_name": "makershub_sync"},
        }
        if settings.dbUsePgBouncer:
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs.update({
                "pool_size": 2,
                "max_overflow": 3,
                "pool_recycle": 1800,
                "pool_timeout": 30,
            })
        _sync_engine = create_engine(connection_url, **engine_kwargs)
    return _sync_engine


# Resultados de uma tentativa de escrita do historico/notificacao (ver
# _run_routing_history_insert). "exists" NAO e falha: a linha ja estava la
# (retry do mesmo agendamento ou DAG Airflow que chegou primeiro).
ROUTING_WRITE_INSERTED = "inserted"
ROUTING_WRITE_EXISTS = "exists"
ROUTING_WRITE_ADVISOR_MISSING = "advisor_missing"


def _is_sf_sandbox() -> bool:
    return os.getenv("SF_IS_SANDBOX", "false").lower() in ("true", "1", "yes")


def record_routing_post_action_pending(
    action: str,
    opportunity_id: str,
    payload: Dict[str, Any],
    error: Optional[str],
    attempt_at: Optional[Any] = None,
) -> bool:
    """Grava a pendencia duravel de uma escrita pos-agendamento que falhou.

    Best-effort e sincrono: NUNCA levanta. Se ate a gravacao da pendencia falha,
    loga em ERRO e devolve False (o agendamento ja foi dado como feito; o log e
    o unico vestigio nesse caso). `payload` leva tudo que a funcao precisa para
    repetir a chamada; "sandbox" marca em qual ambiente ela foi originada, para
    o reprocessador nao misturar sandbox com producao.

    `attempt_at` (so o historico de reroute): o instante, no relogio do BANCO, em
    que a tentativa que falhou comecou (`_db_clock_now`). Vira o `payload_at` da
    pendencia, contra o qual o reprocessador procura um roteamento mais novo.
    """
    from app.repositories import routing_post_action_repo

    try:
        full_payload = {**payload, "sandbox": _is_sf_sandbox()}
        with _get_sync_engine().begin() as conn:
            routing_post_action_repo.record_pending(
                conn,
                opportunity_id=opportunity_id,
                action=action,
                payload=full_payload,
                error=(error or "")[:2000] or None,
                attempt_at=attempt_at,
            )
        logger.warning(
            "[routing-pending] Recorded: action=%s opp=%s error=%s",
            action, opportunity_id, error,
        )
        return True
    except Exception as pending_err:
        # Classe, SQLSTATE e referencia, nunca a mensagem nem o traceback: a de uma
        # falha de statement traz o SQL e os `[parameters: ...]`, e o payload desta
        # pendencia tem o nome do cliente e o patrimonio.
        logger.error(
            "[routing-pending] COULD NOT record pending action=%s opp=%s "
            "(original error: %s): %s",
            action, opportunity_id, error,
            routing_post_action_repo.error_reference(pending_err),
        )
        return False


def _db_clock_now() -> Any:
    """Hora do relogio do BANCO agora (`clock_timestamp()`), a mesma base de
    `routed_at` e `payload_at`. Levanta se nao conseguir ler: quem chama NAO cai para
    outro relogio (o do app, o da gravacao da pendencia), porque instantes de relogios
    diferentes nao se comparam."""
    with _get_sync_engine().connect() as conn:
        return conn.execute(text("SELECT clock_timestamp()")).scalar_one()


def _run_routing_history_insert(
    opportunity_id: str,
    advisor_salesforce_id: str,
    patrimony_value: float,
    routing_source: str = "super-r1",
    opportunity_type: str = "lead",
    reroute: bool = False,
    conn: Any = None,
) -> str:
    """Executa a escrita do historico e devolve ROUTING_WRITE_*; levanta em erro.

    Corpo de `insert_routing_history` sem o tratamento de falha: o reprocessador
    (routing_post_action_service) precisa distinguir excecao, "ja existe" e
    "assessor ausente em dim_employee_scd2", que o bool publico nao separa.

    `conn`: conexao de uma transacao ja aberta pelo chamador (o reprocessador, que
    segura o lock por OPP, confere supersessao e marca a pendencia na mesma
    transacao). Sem `conn`, abre e fecha a propria transacao.
    """
    from app.repositories import routing_post_action_repo

    engine = _get_sync_engine()
    sf_is_sandbox = _is_sf_sandbox()
    history_table = "makershub.sb_routing_history" if sf_is_sandbox else "public.stg_salesforce__routing_history"
    dedup_table = history_table  # check duplicates against same table

    # A tabela de PRODUCAO foi renomeada na onda FBI-2722 (level->seniority_level,
    # net_worth->declared_net_worth_amount); a sandbox sb_routing_history manteve
    # os nomes antigos (medido via information_schema em 2026-08-21).
    level_col = "level" if sf_is_sandbox else "seniority_level"
    net_worth_col = "net_worth" if sf_is_sandbox else "declared_net_worth_amount"

    stmt = text(f"""
        INSERT INTO {history_table} (
            opportunity_id, owner_id, employee_id, {level_col}, routed_at, {net_worth_col},
            routing_source, opportunity_type
        )
        SELECT
            :opportunity_id,
            :owner_id,
            de.employee_id,
            de.level,
            clock_timestamp(),
            :net_worth,
            :routing_source,
            :opportunity_type
        FROM public.dim_employee_scd2 de
        WHERE de.salesforce_user_id = :owner_id
          AND de.is_current = true
          AND NOT EXISTS (
              SELECT 1
              FROM {dedup_table}
              WHERE opportunity_id = :opportunity_id
                AND (
                    NOT :reroute
                    OR (
                        owner_id = :owner_id
                        AND routed_at >= NOW() - INTERVAL '24 hours'
                    )
                )
          )
        LIMIT 1;
    """)

    production_reroute = reroute and not sf_is_sandbox
    if production_reroute:
        # Uma instrucao so: a CTE arquiva a linha antiga em
        # makershub._routing_history_archive quando, e so quando, o DO UPDATE
        # abaixo se aplicaria (mesma condicao do WHERE dele, e o assessor existe
        # para o SELECT gerar a linha). Primeiro roteamento e retry do mesmo dono
        # em menos de 24h nao arquivam nada. O lock por OPP (abaixo) torna
        # leitura-da-linha-antiga + escrita atomicas sob concorrencia.
        stmt = text(  # sql-inline-ok: a f-string interpola so os identificadores internos history_table/level_col/net_worth_col (constantes deste modulo, sem input de usuario); os valores vao por bind param.
            f"""
            WITH archived AS (
                INSERT INTO makershub._routing_history_archive (
                    opportunity_id, owner_id, employee_id, seniority_level, routed_at,
                    declared_net_worth_amount, routing_source, opportunity_type,
                    superseded_by_owner_id
                )
                SELECT
                    prev.opportunity_id, prev.owner_id, prev.employee_id, prev.{level_col},
                    prev.routed_at, prev.{net_worth_col}, prev.routing_source,
                    prev.opportunity_type, :owner_id
                FROM {history_table} prev
                WHERE prev.opportunity_id = :opportunity_id
                  AND EXISTS (
                      SELECT 1
                      FROM public.dim_employee_scd2 adv
                      WHERE adv.salesforce_user_id = :owner_id
                        AND adv.is_current = true
                  )
                  AND (
                      prev.owner_id IS DISTINCT FROM :owner_id
                      OR prev.routed_at < NOW() - INTERVAL '24 hours'
                  )
            )
            INSERT INTO {history_table} (
                opportunity_id, owner_id, employee_id, {level_col}, routed_at, {net_worth_col},
                routing_source, opportunity_type
            )
            SELECT
                :opportunity_id,
                :owner_id,
                de.employee_id,
                de.level,
                clock_timestamp(),
                :net_worth,
                :routing_source,
                :opportunity_type
            FROM public.dim_employee_scd2 de
            WHERE de.salesforce_user_id = :owner_id
              AND de.is_current = true
            LIMIT 1
            ON CONFLICT (opportunity_id) DO UPDATE SET
                owner_id = EXCLUDED.owner_id,
                employee_id = EXCLUDED.employee_id,
                {level_col} = EXCLUDED.{level_col},
                routed_at = EXCLUDED.routed_at,
                {net_worth_col} = EXCLUDED.{net_worth_col},
                routing_source = EXCLUDED.routing_source,
                opportunity_type = EXCLUDED.opportunity_type
            WHERE {history_table}.owner_id IS DISTINCT FROM EXCLUDED.owner_id
               OR {history_table}.routed_at < NOW() - INTERVAL '24 hours';
            """
        )

    def _write(active_conn: Any) -> str:
        if production_reroute:
            routing_post_action_repo.lock_opportunity(active_conn, opportunity_id)
        result = active_conn.execute(stmt, {
            "opportunity_id": opportunity_id,
            "owner_id": advisor_salesforce_id,
            "net_worth": patrimony_value,
            "routing_source": routing_source,
            "opportunity_type": opportunity_type,
            "reroute": reroute,
        })
        if result.rowcount > 0:
            return ROUTING_WRITE_INSERTED
        # Zero linhas: ou a OPP ja estava roteada (dedupe, nao e falha) ou o
        # assessor nao tem linha vigente em dim_employee_scd2 (falha: sem isso o
        # historico nunca sera escrito).
        if routing_post_action_repo.advisor_is_current(active_conn, advisor_salesforce_id):
            return ROUTING_WRITE_EXISTS
        return ROUTING_WRITE_ADVISOR_MISSING

    if conn is not None:
        return _write(conn)
    with engine.begin() as own_conn:
        return _write(own_conn)


def insert_routing_history(
    opportunity_id: str,
    advisor_salesforce_id: str,
    patrimony_value: float,
    routing_source: str = "super-r1",
    opportunity_type: str = "lead",
    reroute: bool = False,
    *,
    record_pending: bool = True,
    exists_ok: bool = False,
) -> bool:
    """
    Insert a record into public.stg_salesforce__routing_history.

    This mirrors what the Airflow DAG (salesforce_opp_routing) does in
    `inserir_registros` — it records that an opportunity was routed to an
    advisor, with employee_id and level resolved from dim_employee_scd2.

    Uses a synchronous DB connection because this runs inside the sync
    executor context of execute_r1_scheduling_flow.

    `reroute` (FBI-4719): uma OPP reaproveitada já tem a linha do
    roteamento original, e a dedupe padrão — qualquer linha da OPP — pularia o
    log do re-roteamento em silêncio. No re-roteamento a dedupe vira "a mesma
    OPP já roteada para ESTE dono nas últimas 24h": cobre o retry do mesmo
    agendamento (minutos depois) sem engolir um re-roteamento legítimo. A produção
    tem a constraint uk_opportunity_id UNIQUE (opportunity_id), então o
    re-roteamento usa UPSERT para atualizar essa linha, apenas quando o dono
    muda ou o roteamento anterior tem mais de 24h. A sandbox não tem essa
    constraint e mantém o INSERT com dedupe por dono e janela de 24h.

    O UPSERT de produção arquiva a linha antiga em
    makershub._routing_history_archive (insert-only) na mesma transação, antes de
    sobrescrever: o histórico de todos os roteamentos de uma OPP fica
    reconstruível.

    Pendência durável (`record_pending`): quando a escrita falha por exceção, ou
    não insere porque o assessor não está em dim_employee_scd2, grava uma linha
    em makershub._routing_post_action_pending para o reprocessador repetir. "Já
    existe" (dedupe) não é falha e não grava nada. O retorno continua sendo só o
    bool de "inseriu"; o reprocessador usa _run_routing_history_insert, que
    distingue os três desfechos.
    """
    from app.repositories import routing_post_action_repo

    payload = {
        "advisor_salesforce_id": advisor_salesforce_id,
        "patrimony_value": patrimony_value,
        "routing_source": routing_source,
        "opportunity_type": opportunity_type,
        "reroute": reroute,
    }
    # O reprocessador decide se um roteamento mais novo ja esta no historico
    # comparando `routed_at` (relogio do banco na escrita) com o instante em que ESTA
    # tentativa comecou, lido do mesmo relogio ANTES de escrever. So o reroute tem
    # supersessao. Se a hora nao puder ser lida, a pendencia leva a marca
    # `attempt_clock_unavailable` e o reprocessador nao a repete (fail-closed).
    attempt_at = None
    if reroute:
        try:
            attempt_at = _db_clock_now()
        except Exception as clock_err:
            logger.error(
                "[routing-history] Could not read the database clock for opp=%s (%s); "
                "a pending reroute will not be repeated automatically",
                opportunity_id, type(clock_err).__name__,
            )
            payload["attempt_clock_unavailable"] = True
    try:
        outcome = _run_routing_history_insert(
            opportunity_id, advisor_salesforce_id, patrimony_value,
            routing_source, opportunity_type, reroute,
        )
    except Exception as e:
        # So classe, SQLSTATE e ref: a mensagem de um erro de SQL carrega os
        # parametros (patrimonio) e o traceback repetiria a mensagem.
        failure = routing_post_action_repo.safe_error(e)
        logger.error("[routing-history] Insert failed: %s", failure)
        if record_pending:
            record_routing_post_action_pending(
                "routing_history", opportunity_id, payload,
                failure, attempt_at=attempt_at,
            )
        return False

    if outcome == ROUTING_WRITE_INSERTED:
        logger.info(
            "[routing-history] Inserted: opp=%s, advisor=%s, net_worth=%s",
            opportunity_id, advisor_salesforce_id, patrimony_value,
        )
        return True

    if outcome == ROUTING_WRITE_EXISTS and exists_ok:
        # The caller wants the row to be there and it is (a resend to the same
        # advisor inside the window): nothing failed and nothing is pending.
        logger.info(
            "[routing-history] Already recorded: opp=%s, advisor=%s",
            opportunity_id, advisor_salesforce_id,
        )
        return True
    logger.warning(
        "[routing-history] No row inserted for opp=%s — "
        "either already exists or advisor %s not found in dim_employee_scd2",
        opportunity_id, advisor_salesforce_id,
    )
    if outcome == ROUTING_WRITE_ADVISOR_MISSING and record_pending:
        record_routing_post_action_pending(
            "routing_history", opportunity_id, payload,
            f"advisor {advisor_salesforce_id} not found in dim_employee_scd2",
            attempt_at=attempt_at,
        )
    return False


def _run_routing_notification_insert(
    opportunity_id: str,
    advisor_salesforce_id: str,
    client_name: str,
    patrimony_value: float,
    routed_at: str,
    description: Optional[str] = None,
    investment_interests: Optional[str] = None,
    reroute: bool = False,
    conn: Any = None,
) -> str:
    """Executa a escrita da notificacao e devolve ROUTING_WRITE_*; levanta em erro.

    Corpo de `insert_routing_notification` sem o tratamento de falha, para o
    reprocessador distinguir excecao, "ja existe" e "assessor ausente". `conn`
    funciona como em `_run_routing_history_insert`.
    """
    import json

    engine = _get_sync_engine()

    # Resolve employee_id (employee_id in notifications) from dim_employee_scd2
    resolve_stmt = text("""
        SELECT de.employee_id
        FROM public.dim_employee_scd2 de
        WHERE de.salesforce_user_id = :salesforce_user_id
          AND de.is_current = true
        LIMIT 1
    """)

    insert_stmt = text("""
        INSERT INTO makershub._notification
            (employee_id, title, message, link, notification_type, html_key, is_read, created_at)
        SELECT
            :employee_id,
            'Nova Oportunidade!',
            :message_json,
            :salesforce_link,
            'routing',
            :html_key,
            false,
            NOW()
        WHERE NOT EXISTS (
            SELECT 1
            FROM makershub._notification
            WHERE notification_type = 'routing'
                AND message::jsonb->>'opportunity_id' = :opportunity_id
                AND (
                    NOT :reroute
                    OR (
                        employee_id = :employee_id
                        AND created_at >= NOW() - INTERVAL '24 hours'
                    )
                )
        )
    """)

    def _write(conn: Any) -> str:
        row = conn.execute(resolve_stmt, {
            "salesforce_user_id": advisor_salesforce_id,
        }).fetchone()

        if not row:
            logger.warning(
                "[routing-notification] Advisor %s not found in dim_employee_scd2",
                advisor_salesforce_id,
            )
            return ROUTING_WRITE_ADVISOR_MISSING

        employee_id = row.employee_id

        message_json = json.dumps({
            "opportunity_id": opportunity_id,
            "client_name": client_name,
            "pl": patrimony_value,
            "routed_at": routed_at,
            "description": description,
            "investment_interests": investment_interests,
        })

        salesforce_link = (
            f"https://fazcapital.my.site.com/portal/s/opportunity/{opportunity_id}/"
        )

        result = conn.execute(insert_stmt, {
            "employee_id": employee_id,
            "message_json": message_json,
            "salesforce_link": salesforce_link,
            "html_key": "routing_template",
            "opportunity_id": opportunity_id,
            "reroute": reroute,
        })

        if result.rowcount > 0:
            logger.info(
                "[routing-notification] Created: employee_id=%s, opp=%s",
                employee_id, opportunity_id,
            )
            return ROUTING_WRITE_INSERTED
        logger.warning(
            "[routing-notification] No row inserted for opp=%s — "
            "notification already exists",
            opportunity_id,
        )
        return ROUTING_WRITE_EXISTS

    if conn is not None:
        return _write(conn)
    with engine.begin() as own_conn:
        return _write(own_conn)


def insert_routing_notification(
    opportunity_id: str,
    advisor_salesforce_id: str,
    client_name: str,
    patrimony_value: float,
    routed_at: str,
    description: Optional[str] = None,
    investment_interests: Optional[str] = None,
    reroute: bool = False,
    *,
    record_pending: bool = True,
    exists_ok: bool = False,
) -> bool:
    """
    Insert a routing notification into makershub._notification.

    Mirrors what the Airflow DAG (routing_notifications) does in
    `create_notifications` — notifies the advisor that a new opportunity
    was routed to them.

    Uses a synchronous DB connection because this runs inside the sync
    executor context of execute_r1_scheduling_flow.

    Quando a escrita falha por exceção, ou não acontece porque o assessor não
    resolve em dim_employee_scd2, grava a pendência durável em
    makershub._routing_post_action_pending (`record_pending`) para o
    reprocessador repetir. "Já existe" (dedupe) devolve False, ou True com
    `exists_ok` (quem chama quer a notificação lá e ela está: não é falha).
    """
    from app.repositories import routing_post_action_repo

    payload = {
        "advisor_salesforce_id": advisor_salesforce_id,
        "client_name": client_name,
        "patrimony_value": patrimony_value,
        "routed_at": routed_at,
        "description": description,
        "investment_interests": investment_interests,
        "reroute": reroute,
    }
    try:
        outcome = _run_routing_notification_insert(
            opportunity_id, advisor_salesforce_id, client_name, patrimony_value,
            routed_at, description, investment_interests, reroute,
        )
    except Exception as e:
        # So classe, SQLSTATE e ref: a mensagem de um erro de SQL carrega os
        # parametros (nome do cliente, patrimonio) e o traceback a repetiria.
        failure = routing_post_action_repo.safe_error(e)
        logger.error("[routing-notification] Insert failed: %s", failure)
        if record_pending:
            record_routing_post_action_pending(
                "routing_notification", opportunity_id, payload, failure,
            )
        return False
    if outcome == ROUTING_WRITE_ADVISOR_MISSING and record_pending:
        record_routing_post_action_pending(
            "routing_notification", opportunity_id, payload,
            f"advisor {advisor_salesforce_id} not found in dim_employee_scd2",
        )
    if outcome == ROUTING_WRITE_EXISTS and exists_ok:
        logger.info(
            "[routing-notification] Already recorded: opp=%s, advisor=%s",
            opportunity_id, advisor_salesforce_id,
        )
        return True
    return outcome == ROUTING_WRITE_INSERTED


def resolve_sandbox_lead_id(
    sf: Salesforce,
    lead_email: Optional[str],
    lead_name: Optional[str],
) -> Optional[str]:
    """
    When running against the Salesforce sandbox, production Lead IDs don't exist.
    This function resolves the matching sandbox lead by email (preferred) or name.

    Returns the sandbox Lead ID or None if not found.
    """
    # Try by email first (most reliable)
    if lead_email:
        safe_email = _esc_soql(lead_email)
        result = sf.query(
            f"SELECT Id, Name, Email FROM Lead "
            f"WHERE Email = '{safe_email}' AND IsConverted = false "
            f"ORDER BY CreatedDate DESC LIMIT 1"
        )
        if result.get("totalSize", 0) > 0:
            sandbox_id = result["records"][0]["Id"]
            logger.info(
                "Sandbox lead resolved by email '%s' → %s (%s)",
                lead_email, sandbox_id, result["records"][0]["Name"],
            )
            return sandbox_id

    # Fallback: try by name
    if lead_name:
        safe_name = _esc_soql(lead_name)
        result = sf.query(
            f"SELECT Id, Name, Email FROM Lead "
            f"WHERE Name = '{safe_name}' AND IsConverted = false "
            f"ORDER BY CreatedDate DESC LIMIT 1"
        )
        if result.get("totalSize", 0) > 0:
            sandbox_id = result["records"][0]["Id"]
            logger.info(
                "Sandbox lead resolved by name '%s' → %s",
                lead_name, sandbox_id,
            )
            return sandbox_id

    logger.warning(
        "Could not resolve sandbox lead for email=%s, name=%s",
        lead_email, lead_name,
    )
    return None


def _resolve_active_user_id_by_email(sf: Salesforce, user_email: str) -> Optional[str]:
    """Query SF for the canonical internal User by Email, returning the Id (or None)."""
    try:
        rec = resolve_sf_user_by_email(sf, user_email, ("Id",))
        return rec["Id"] if rec else None
    except Exception as e:
        logger.warning("User lookup by email '%s' failed: %s", user_email, e)
        return None


def _ensure_sdr_team_member(
    sf: Salesforce,
    *,
    opportunity_id: str,
    real_sdr_sf_id: str,
    sdr_email: Optional[str],
    advisor_salesforce_id: Optional[str],
    steps_completed: List[str],
    errors: List[str],
) -> None:
    """
    Ensure an OpportunityTeamMember exists with role='SDR' for the SDR user.

    Why this is non-trivial:
      Salesforce's `convertLead` creates the new Opportunity with OwnerId
      derived from the Lead, so SF auto-creates `{SDR_user, "Opportunity Owner"}`
      on the new Opp before the backend can intervene. The unique constraint
      on (OpportunityId, UserId) means the SDR cannot then be inserted with
      role='SDR' — it would collide with the auto-created OppOwner record.
      Worse, that auto-created record gets deleted later by a SF Flow that
      cleans up "Opportunity Owner" rows whose UserId != current OwnerId,
      leaving the opp with no SDR row at all.

    Pattern (delete-blocker-then-insert with race recovery):
      1. Query any record on this opp where UserId == real_sdr OR role == 'SDR'.
      2. Delete records that block us:
         - SDR's own record with role != 'SDR' (auto-OppOwner from convertLead).
         - 'SDR'-role records pointing to a different user (legacy cleanup).
         If the SDR already has role='SDR', record that as idempotent success.
      3. Insert {opp, real_sdr, 'SDR'}.
      4. On DUPLICATE_VALUE (race vs the keepSDROpportunityTeam queueable
         re-inserting after the lead-conversion or owner-change trigger),
         re-query, re-clean blockers, retry insert once.

    All failures are non-blocking: logged + appended to `errors`, but we
    don't raise — the rest of the post-opp flow must continue.
    """
    _validate_sf_id(opportunity_id)
    # Escape at the sink despite the upstream validations: opportunity_id is
    # regex-checked above and real_sdr_sf_id is a Salesforce-resolved Id, but
    # SOQL string literals here must stay unbreakable even if either invariant
    # regresses (defense in depth, same rationale as _esc_soql's "Fase 3.6").
    safe_opportunity_id = _esc_soql(opportunity_id)
    safe_real_sdr_sf_id = _esc_soql(real_sdr_sf_id or "")

    # Step 1: read state
    existing: List[Dict[str, Any]] = []
    try:
        existing = sf.query(
            f"SELECT Id, UserId, TeamMemberRole FROM OpportunityTeamMember "
            f"WHERE OpportunityId = '{safe_opportunity_id}' "
            f"AND (UserId = '{safe_real_sdr_sf_id}' OR TeamMemberRole = 'SDR')"
        ).get("records", [])
    except Exception as q_err:
        logger.warning(
            "POST-OPP[opp=%s]: Pre-insert SDR query failed: %s",
            opportunity_id, q_err,
        )

    # Step 2: short-circuit if already correct
    for rec in existing:
        if rec.get("UserId") == real_sdr_sf_id and rec.get("TeamMemberRole") == "SDR":
            logger.info(
                "POST-OPP[opp=%s]: SDR team member already correct (Id=%s) — no change",
                opportunity_id, rec.get("Id"),
            )
            steps_completed.append("sdr_team_member_exists")
            return

    # Step 3: delete blockers
    for rec in existing:
        rec_id = rec.get("Id")
        rec_user = rec.get("UserId")
        rec_role = rec.get("TeamMemberRole")
        is_blocker = (
            (rec_user == real_sdr_sf_id and rec_role != "SDR")  # SDR with wrong role (auto-OppOwner)
            or (rec_user != real_sdr_sf_id and rec_role == "SDR")  # other user with SDR role
        )
        if not is_blocker:
            continue
        try:
            sf.OpportunityTeamMember.delete(rec_id)  # type: ignore
            logger.info(
                "POST-OPP[opp=%s]: Removed blocker team member %s (user=%s, role=%s)",
                opportunity_id, rec_id, rec_user, rec_role,
            )
        except Exception as del_err:
            logger.warning(
                "POST-OPP[opp=%s]: Could not delete blocker %s: %s",
                opportunity_id, rec_id, del_err,
            )

    # Step 4: insert with retry on race
    for attempt in (1, 2):
        try:
            new_member = sf.OpportunityTeamMember.create({  # type: ignore
                "OpportunityId": opportunity_id,
                "UserId": real_sdr_sf_id,
                "TeamMemberRole": "SDR",
                "OpportunityAccessLevel": "Edit",
            })
            logger.info(
                "POST-OPP[opp=%s]: Created SDR team member %s for user %s (attempt=%d)",
                opportunity_id, new_member.get("id"), real_sdr_sf_id, attempt,
            )
            steps_completed.append("sdr_team_member_fixed")
            return
        except Exception as create_err:
            err_str = str(create_err)
            is_duplicate = (
                "DUPLICATE_VALUE" in err_str
                or "duplicate" in err_str.lower()
                or "already exists" in err_str.lower()
            )
            if is_duplicate and attempt == 1:
                # Race vs keepSDROpportunityTeam queueable: re-query and re-clean.
                logger.info(
                    "POST-OPP[opp=%s]: SDR insert hit duplicate; re-cleaning before retry",
                    opportunity_id,
                )
                try:
                    racers = sf.query(
                        f"SELECT Id, TeamMemberRole FROM OpportunityTeamMember "
                        f"WHERE OpportunityId = '{safe_opportunity_id}' "
                        f"AND UserId = '{safe_real_sdr_sf_id}'"
                    ).get("records", [])
                    for r in racers:
                        if r.get("TeamMemberRole") == "SDR":
                            logger.info(
                                "POST-OPP[opp=%s]: SDR landed during race (Id=%s) — done",
                                opportunity_id, r.get("Id"),
                            )
                            steps_completed.append("sdr_team_member_exists")
                            return
                        try:
                            sf.OpportunityTeamMember.delete(r["Id"])  # type: ignore
                        except Exception:
                            pass
                except Exception as recovery_err:
                    logger.warning(
                        "POST-OPP[opp=%s]: Race recovery failed: %s",
                        opportunity_id, recovery_err,
                    )
                # fall through to attempt 2
                continue
            # Non-duplicate failure or already retried
            logger.error(
                "POST-OPP[opp=%s]: Failed to create SDR team member "
                "(user=%s, email=%s, advisor_owner=%s, attempt=%d): %s",
                opportunity_id, real_sdr_sf_id, sdr_email, advisor_salesforce_id,
                attempt, create_err, exc_info=True,
            )
            errors.append(
                f"SDR team member não criado (opp {opportunity_id}): {create_err}"
            )
            return


# O que precisa estar feito no Salesforce para um R1 existir de verdade: o
# assessor é dono dos registros, o Event está na agenda e a Opp mudou de fase.
# É a definição de "desired outcome" do docs/reference/SUPER_R1_FLOWS.md (Flow 1), e é o
# gate dos fluxos interativos.
#
# routing_history_inserted NÃO entra aqui de propósito: é uma escrita no
# Postgres, independente do Salesforce, então pode falhar sozinha com o R1 já
# marcado. Num fluxo interativo, reprovar por isso faria o SDR ver "Falha no
# agendamento" e remarcar, criando Opportunity e Event duplicados na agenda do
# assessor — exatamente o que a prevenção de duplicidade do fluxo existe para
# evitar. Bookkeeping que falha vira erro em `errors`, não reprovação.
R1_CRITICAL_STEPS = frozenset({
    "ownership_transferred",
    "event_created",
    "opportunity_updated",
})

# O lote D+1 pode ser mais estrito: lá uma reprovação só marca a linha como
# sf_error e a própria rodada seguinte reprocessa, sem humano remarcando. Por
# isso o histórico de roteamento entra no gate do finalize.
R1_FINALIZE_CRITICAL_STEPS = R1_CRITICAL_STEPS | {"routing_history_inserted"}

# H-004 (PR #594): steps that do NOT fail the R1 (they stay out of
# R1_CRITICAL_STEPS for the reason above) but whose absence the business feels:
# the OPP keeps the new owner and Event together with the fields of the previous
# qualification. When one of them fails AFTER the booking is done, the flow
# result carries its stable name in `partial_steps` and `success` stays True.
# The caller that builds the response decides whether re-submitting completes
# it (only the Opportunity entry, where a re-submission reuses Event and advisor).
PARTIAL_STEP_CONSORCIO_FIELDS = "consorcio_fields"
# Reused OPP whose stage / meeting status could not be re-read before the PATCH:
# they were left as they are in Salesforce (H-006).
PARTIAL_STEP_OPPORTUNITY_STAGE = "opportunity_stage"


def _mark_partial_step(
    flow_result: Dict[str, Any], steps_completed: List[str], name: str
) -> None:
    """Record `name` in `flow_result["partial_steps"]` if the R1 is already booked.

    "Booked" means the whole critical set is in the completed steps. Before that
    the flow already fails by itself and a re-submission redoes everything; a
    name in `partial_steps` there would describe a partial booking that does not
    exist.
    """
    if not R1_CRITICAL_STEPS.issubset(set(steps_completed)):
        return
    partial: List[str] = flow_result.setdefault("partial_steps", [])
    if name not in partial:
        partial.append(name)


def _execute_post_opportunity_steps(
    *,
    sf: Salesforce,
    sf_is_sandbox: bool,
    opportunity_id: str,
    account_id: Optional[str],
    contact_id: Optional[str],
    advisor_salesforce_id: str,
    advisor_name: str,
    sdr_salesforce_id: str,
    sdr_name: str,
    sdr_email: Optional[str],
    client_name: str,
    patrimony_value: float,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    event_datetime: datetime,
    duration_minutes: int,
    modalidade: str,
    is_consorcio: bool,
    opportunity_type: str,
    flow_result: Dict[str, Any],
    steps_completed: List[str],
    errors: List[str],
    # Consórcio fields — written directly to Opp when no Lead conversion copies them
    idade: Optional[int] = None,
    modalidade_calculo: Optional[str] = None,
    id_carta: Optional[int] = None,
    tomador_decisao: Optional[str] = None,
    intuito_consorcio: Optional[str] = None,
    interesses_consorcios: Optional[str] = None,
    reused_opportunity: bool = False,
    source_opp_state: Optional[ReusedOpportunityState] = None,
    resuming_converted_lead: bool = False,
) -> None:
    """
    Shared post-opportunity steps used by both Lead and Account flows.

    Executes: ownership transfer, event creation, opportunity update,
    SDR team member fix, account team member (consórcio), consórcio fields,
    routing history, and routing notification.

    `reused_opportunity` (FBI-4719): a OPP veio de entrada e não foi criada
    agora — preserva a descrição do assessor e grava o histórico como
    re-roteamento (ver insert_routing_history).

    `resuming_converted_lead`: the resend of a converted Lead resumes the Opportunity
    whose history and notification the first attempt already wrote. As with a reused
    Opportunity, "already exists" is the wanted state, not a failure (`exists_ok`).
    """
    # ─── EARLY: Resolve SDR + ensure SDR team member with role='SDR' BEFORE owner change ───
    # The SDR team-member fix MUST happen before update_opportunity_after_conversion
    # (which changes Owner to the advisor). Otherwise the SDR-as-OppOwner record auto-
    # created by Lead conversion gets harvested by the cleanup Flow that runs 1 min
    # after the owner change. See _ensure_sdr_team_member docstring for full rationale.
    real_sdr_sf_id: Optional[str] = _resolve_active_user_id_by_email(sf, sdr_email) if sdr_email else None
    if real_sdr_sf_id:
        logger.info(
            "POST-OPP[opp=%s]: SDR resolved to %s — ensuring team member before owner change",
            opportunity_id, real_sdr_sf_id,
        )
        try:
            _ensure_sdr_team_member(
                sf,
                opportunity_id=opportunity_id,
                real_sdr_sf_id=real_sdr_sf_id,
                sdr_email=sdr_email,
                advisor_salesforce_id=advisor_salesforce_id,
                steps_completed=steps_completed,
                errors=errors,
            )
        except Exception as e:
            logger.error(
                "POST-OPP[opp=%s]: Unexpected error in early SDR team member ensure: %s",
                opportunity_id, e, exc_info=True,
            )
            errors.append(f"Erro inesperado ao garantir SDR team member: {e}")
    else:
        logger.warning(
            "POST-OPP[opp=%s]: SDR (%s / %s) not resolved as active SF User — skipping SDR team member",
            opportunity_id, sdr_name, sdr_email,
        )

    # ─── Transfer Account & Contact ownership to advisor ───
    logger.info(
        "POST-OPP: Transferring Account/Contact ownership to advisor %s (%s)...",
        advisor_salesforce_id, advisor_name,
    )
    try:
        ownership_res = update_ownership_after_conversion(
            sf=sf,
            account_id=account_id,
            contact_id=contact_id,
            advisor_salesforce_id=advisor_salesforce_id,
            advisor_name=advisor_name,
        )
        if ownership_res.get("success"):
            steps_completed.append("ownership_transferred")
            logger.info("POST-OPP: Ownership transferred: %s", ownership_res.get("updated"))
        else:
            errors.append(
                f"Falha parcial na transferência de propriedade: "
                f"Account={ownership_res.get('account_error', 'OK')}, "
                f"Contact={ownership_res.get('contact_error', 'OK')}"
            )
            logger.warning("POST-OPP: Partial ownership failure: %s", ownership_res)
    except Exception as e:
        errors.append(f"Erro na transferência de propriedade: {e}")
        logger.error("POST-OPP (ownership transfer) error: %s", e, exc_info=True)

    # ─── Create R1 Event ───
    # IMPORTANT: Event MUST be created BEFORE advancing Opportunity stage.
    # SF validation rule: "Para avançar a Fase é necessário marcar a R1 com o cliente!"
    logger.info("POST-OPP: Creating R1 event for opportunity %s...", opportunity_id)
    # Once the network write starts, an exception is not negative proof: SF
    # may have committed before the response was lost. Keep it unknown unless
    # Salesforce returns an explicit negative result or a durable Event id.
    flow_result["event_write_outcome"] = "write_started_unknown"
    try:
        event_res = create_r1_event(
            sf=sf,
            opportunity_id=opportunity_id,
            contact_id=contact_id,
            advisor_salesforce_id=advisor_salesforce_id,
            event_datetime=event_datetime,
            description=description,
            duration_minutes=duration_minutes,
            modalidade=modalidade,
        )
        if event_res.get("success"):
            flow_result["event_id"] = event_res["event_id"]
            flow_result["event_write_outcome"] = "event_created"
            steps_completed.append("event_created")
            logger.info("POST-OPP: Event created: %s", event_res["event_id"])
        else:
            flow_result["event_write_outcome"] = event_res.get(
                "event_write_outcome", "event_not_created"
            )
            errors.append(f"Falha ao criar Event: {event_res.get('message')}")
            logger.error("POST-OPP: Event creation failed: %s", event_res.get("message"))
    except Exception as e:
        errors.append(f"Erro ao criar Event: {e}")
        logger.error("POST-OPP (create event) error: %s", e, exc_info=True)

    # ─── Update Opportunity (stage, owner, fields) ───
    logger.info("POST-OPP: Updating opportunity %s...", opportunity_id)
    try:
        if reused_opportunity:
            opp_state = _fresh_reused_opportunity_state(sf, opportunity_id, source_opp_state)
            stage_state_unknown = opp_state is None
        else:
            opp_state, stage_state_unknown = source_opp_state, False
        opp_res = update_opportunity_after_conversion(
            sf=sf,
            opportunity_id=opportunity_id,
            advisor_salesforce_id=advisor_salesforce_id,
            advisor_name=advisor_name,
            sdr_name=sdr_name,
            patrimony_value=patrimony_value,
            profissao=profissao,
            interesse_investimentos=interesse_investimentos,
            description=description,
            is_consorcio=is_consorcio,
            reused_opportunity=reused_opportunity,
            current_state=opp_state,
            stage_state_unknown=stage_state_unknown,
        )
        if opp_res.get("success"):
            steps_completed.append("opportunity_updated")
            if stage_state_unknown:
                _mark_partial_step(flow_result, steps_completed, PARTIAL_STEP_OPPORTUNITY_STAGE)
            logger.info("POST-OPP: Opportunity %s updated (owner → %s)", opportunity_id, advisor_name)
        else:
            errors.append(f"Falha ao atualizar Opportunity: {opp_res.get('message')}")
            logger.error("POST-OPP: Opp update failed: %s", opp_res.get("message"))
    except Exception as e:
        errors.append(f"Erro ao atualizar Opportunity: {e}")
        logger.error("POST-OPP (update opp) error: %s", e, exc_info=True)

    # ─── Write consórcio fields directly to Opportunity ───
    # For Lead flow: SF copies these during conversion, so consórcio params are None.
    # For Account flow: no Lead exists, so we write them here.
    consorcio_opp_data: Dict[str, Any] = {
        "Idade__c": idade,
        "ModalidadeCalculo__c": modalidade_calculo,
        "IdCarta__c": id_carta,
        "TomadorDecisao__c": tomador_decisao,
        "IntuitoConsorcio__c": intuito_consorcio,
        "InteressesConsorcios__c": interesses_consorcios,
    }
    consorcio_opp_data = {k: v for k, v in consorcio_opp_data.items() if v is not None}
    if consorcio_opp_data and opportunity_id:
        try:
            sf.Opportunity.update(opportunity_id, consorcio_opp_data)  # type: ignore
            steps_completed.append("consorcio_fields_set")
            logger.info("POST-OPP: Consórcio fields set on Opportunity: %s", list(consorcio_opp_data.keys()))
        except Exception as e:
            errors.append(f"Falha ao definir campos de consórcio: {e}")
            logger.error("POST-OPP (consórcio fields) error: %s", e, exc_info=True)
            _mark_partial_step(flow_result, steps_completed, PARTIAL_STEP_CONSORCIO_FIELDS)

    # SDR team member was ensured early (before owner change). real_sdr_sf_id is in scope.
    # ─── Add SDR as Account Team Member (consórcio only) ───
    # Non-blocking: log + continue on any error.
    if is_consorcio and account_id and real_sdr_sf_id:
        try:
            _validate_sf_id(account_id)
            _validate_sf_id(real_sdr_sf_id)
            try:
                sf.AccountTeamMember.create({  # type: ignore
                    "AccountId": account_id,
                    "UserId": real_sdr_sf_id,
                    "TeamMemberRole": "SDR",
                    "AccountAccessLevel": "Edit",
                    "OpportunityAccessLevel": "Edit",
                })
                steps_completed.append("sdr_account_team_member_added")
                logger.info(
                    "POST-OPP[opp=%s, acct=%s]: Added SDR %s as Account Team Member",
                    opportunity_id, account_id, real_sdr_sf_id,
                )
            except Exception as create_err:
                err_str = str(create_err)
                if "DUPLICATE_VALUE" in err_str or "duplicate" in err_str.lower() or "already exists" in err_str.lower():
                    logger.info("POST-OPP[acct=%s]: SDR already on Account Team (idempotent)", account_id)
                    steps_completed.append("sdr_account_team_member_exists")
                else:
                    logger.error(
                        "POST-OPP[acct=%s]: Failed to add SDR %s as AccountTeamMember: %s",
                        account_id, real_sdr_sf_id, create_err, exc_info=True,
                    )
                    errors.append(f"SDR não adicionado à equipe da conta {account_id}: {create_err}")
        except Exception as e:
            logger.error(
                "POST-OPP[acct=%s]: Unexpected error in Account Team Member logic: %s",
                account_id, e, exc_info=True,
            )
            errors.append(f"Erro inesperado em Account Team Member: {e}")

    # ─── Insert routing history record ───
    if opportunity_id and advisor_salesforce_id:
        logger.info("POST-OPP: Inserting routing history for opp %s...%s", opportunity_id, " [SANDBOX]" if sf_is_sandbox else "")
        try:
            rh_ok = insert_routing_history(
                opportunity_id=opportunity_id,
                advisor_salesforce_id=advisor_salesforce_id,
                patrimony_value=patrimony_value,
                opportunity_type=opportunity_type,
                reroute=reused_opportunity,
                # A resend to the same advisor inside the window finds the row it
                # wrote the first time: that is the state the caller wants, not an
                # error (the confirmation screen would show a false pendency).
                exists_ok=reused_opportunity or resuming_converted_lead,
            )
            if rh_ok:
                steps_completed.append("routing_history_inserted")
                logger.info("POST-OPP: Routing history inserted")
            else:
                errors.append("Falha ao inserir histórico de roteamento (sem linha inserida)")
                logger.warning("POST-OPP: Routing history not inserted (no row)")
        except Exception as e:
            errors.append(f"Erro ao inserir histórico de roteamento: {e}")
            logger.error("POST-OPP (routing history) error: %s", e, exc_info=True)

    # ─── Insert routing notification ───
    if opportunity_id and advisor_salesforce_id:
        if sf_is_sandbox:
            logger.info("POST-OPP: SKIPPED (sandbox mode) — routing notification not inserted")
            steps_completed.append("routing_notification_skipped_sandbox")
        else:
            logger.info("POST-OPP: Inserting routing notification for opp %s...", opportunity_id)
            try:
                from datetime import timezone
                notif_ok = insert_routing_notification(
                    opportunity_id=opportunity_id,
                    advisor_salesforce_id=advisor_salesforce_id,
                    client_name=client_name,
                    patrimony_value=patrimony_value,
                    routed_at=datetime.now(timezone.utc).isoformat(),
                    description=description,
                    investment_interests=interesse_investimentos,
                    reroute=reused_opportunity,
                    exists_ok=reused_opportunity or resuming_converted_lead,
                )
                if notif_ok:
                    steps_completed.append("routing_notification_inserted")
                    logger.info("POST-OPP: Routing notification inserted")
                else:
                    errors.append("Falha ao inserir notificação de roteamento (sem linha inserida)")
                    logger.warning("POST-OPP: Routing notification not inserted (no row)")
            except Exception as e:
                errors.append(f"Erro ao inserir notificação de roteamento: {e}")
                logger.error("POST-OPP (routing notification) error: %s", e, exc_info=True)


def execute_r1_scheduling_flow(
    lead_id: str,
    lead_name: str,
    lead_email: Optional[str],
    patrimony_value: float,
    patrimony_range: str,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    event_datetime: datetime,
    advisor_salesforce_id: str,
    advisor_name: str,
    sdr_salesforce_id: str,
    sdr_name: str,
    sdr_email: Optional[str] = None,
    lead_source: Optional[str] = None,
    is_consorcio: bool = False,
    duration_minutes: int = MEETING_DURATION,
    modalidade: str = "Online",
    sf_user_connection: Optional[Salesforce] = None,
    # Consórcio-specific fields
    idade: Optional[int] = None,
    modalidade_calculo: Optional[str] = None,
    id_carta: Optional[int] = None,
    tomador_decisao: Optional[str] = None,
    intuito_consorcio: Optional[str] = None,
    interesses_consorcios: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the full R1 scheduling flow in Salesforce (SYNCHRONOUS).

    Must be called via run_in_executor from async context.

    If `sf_user_connection` is provided (JWT per-user auth), all WRITE
    operations use it so that "Created By" shows the real user.
    READ/lookup operations still use the admin connection for reliability.

    Steps:
    1. Connect to Salesforce
    2. Update Lead fields (patrimony, profession, interests, description)
    3. Convert Lead → Opportunity (via Apex REST)
    4. Update Opportunity (owner, meeting status, copied fields)
    5. Create R1 Event linked to Opportunity
    """
    sf_is_sandbox = os.getenv("SF_IS_SANDBOX", "false").lower() in ("true", "1", "yes")

    logger.info(
        "╔══════════════════════════════════════════════════════════════╗"
    )
    logger.info(
        "║  R1 SCHEDULING FLOW — %s",
        "SANDBOX MODE" if sf_is_sandbox else "PRODUCTION MODE",
    )
    logger.info(
        "╠══════════════════════════════════════════════════════════════╣"
    )
    logger.info("║  Lead ID (from DB): %s", lead_id)
    logger.info("║  Lead Name:         %s", lead_name)
    logger.info("║  Lead Email:        %s", lead_email)
    logger.info("║  Patrimony:         %s (%s)", patrimony_value, patrimony_range)
    logger.info("║  Profissão:         %s", profissao)
    logger.info("║  Interesses:        %s", interesse_investimentos)
    logger.info("║  Description:       %s", description[:80] if description else "N/A")
    logger.info("║  Event:             %s (%d min, %s)", event_datetime, duration_minutes, modalidade)
    logger.info("║  Advisor SF ID:     %s (%s)", advisor_salesforce_id, advisor_name)
    logger.info("║  SDR SF ID:         %s (%s)", sdr_salesforce_id, sdr_name)
    logger.info(
        "╚══════════════════════════════════════════════════════════════╝"
    )

    steps_completed: List[str] = []
    errors: List[str] = []
    flow_result: Dict[str, Any] = {
        "success": False,
        "lead_id": lead_id,
        "opportunity_id": None,
        "contact_id": None,
        "event_id": None,
        "event_write_outcome": "event_not_attempted",
        "steps_completed": steps_completed,
        "errors": errors,
        "sandbox_mode": sf_is_sandbox,
    }

    # ─── STEP 0: Connect ───
    # Admin connection for reads/lookups
    sf = get_salesforce_connection()
    if not sf:
        errors.append("Falha na autenticação com Salesforce")
        notify_teams_salesforce_error(
            "Falha na autenticação com Salesforce",
            operation="R1 Scheduling",
        )
        return flow_result
    steps_completed.append("salesforce_connected")

    # Per-user connection for WRITE operations (so "Created By" = real user)
    # Falls back to admin if JWT not configured or user has no SF account
    sf_write = resolve_write_connection(sf, sf_user_connection, sdr_email)
    if sf_user_connection:
        logger.info(
            "STEP 0: Connected — admin=%s, writes-as-user=%s (JWT per-user auth active)",
            sf.sf_instance, sf_user_connection.sf_instance,
        )
        steps_completed.append("jwt_per_user_auth")
    else:
        logger.info(
            "STEP 0: Connected to Salesforce (%s) — writes use admin account",
            sf.sf_instance,
        )

    # ─── STEP 0.5: Resolve sandbox lead ID if needed ───
    actual_lead_id = lead_id
    if sf_is_sandbox:
        sandbox_id = resolve_sandbox_lead_id(sf, lead_email, lead_name)
        if sandbox_id:
            actual_lead_id = sandbox_id
            flow_result["sandbox_lead_id"] = sandbox_id
            logger.info(
                "STEP 0.5: Sandbox mode — resolved prod ID %s → sandbox ID %s",
                lead_id, actual_lead_id,
            )
            steps_completed.append("sandbox_lead_resolved")
        else:
            msg = (
                f"Lead não encontrado no Sandbox "
                f"(email={lead_email}, nome={lead_name}). "
                f"Verifique se os leads foram importados para o sandbox."
            )
            errors.append(msg)
            logger.error("STEP 0.5: %s", msg)
            return flow_result

    # ─── STEP 1: Update Lead ───
    logger.info("STEP 1: Updating lead %s fields...", actual_lead_id)
    try:
        update_res = update_lead_fields(
            sf=sf_write,
            lead_id=actual_lead_id,
            patrimony_value=patrimony_value,
            patrimony_range=patrimony_range,
            profissao=profissao,
            interesse_investimentos=interesse_investimentos,
            description=description,
            is_consorcio=is_consorcio,
            idade=idade,
            modalidade_calculo=modalidade_calculo,
            id_carta=id_carta,
            tomador_decisao=tomador_decisao,
            intuito_consorcio=intuito_consorcio,
            interesses_consorcios=interesses_consorcios,
        )
        if update_res.get("success"):
            steps_completed.append("lead_updated")
            logger.info("STEP 1: Lead %s updated successfully", actual_lead_id)
        else:
            errors.append(f"Falha ao atualizar Lead: {update_res.get('message')}")
            logger.error("STEP 1: Failed to update lead: %s", update_res.get("message"))
    except Exception as e:
        errors.append(f"Erro ao atualizar Lead: {e}")
        logger.error("STEP 1 (update lead) error: %s", e, exc_info=True)

    # ─── STEP 2: Convert Lead → Opportunity ───
    logger.info("STEP 2: Converting lead %s to opportunity...", actual_lead_id)
    try:
        convert_res = convert_lead_to_opportunity(
            sf=sf_write,
            lead_id=actual_lead_id,
            sdr_user_id=sdr_salesforce_id,
            lead_name=lead_name,
            lead_source=lead_source,
        )
        if not convert_res.get("success"):
            errors.append(f"Falha na conversão do Lead: {convert_res.get('message')}")
            logger.error("STEP 2: Conversion failed: %s", convert_res.get("message"))
            return flow_result

        opportunity_id = _validate_sf_id(convert_res["opportunity_id"])
        contact_id = convert_res.get("contact_id")
        if contact_id:
            _validate_sf_id(contact_id)
        flow_result["opportunity_id"] = opportunity_id
        flow_result["contact_id"] = contact_id
        steps_completed.append("lead_converted")
        logger.info(
            "STEP 2: Lead converted! Opp=%s, Contact=%s, Account=%s",
            opportunity_id, contact_id, convert_res.get("account_id"),
        )

    except Exception as e:
        errors.append(f"Erro na conversão do Lead: {e}")
        logger.error("STEP 2 (convert lead) error: %s", e, exc_info=True)
        return flow_result

    # ─── Shared post-creation steps ───
    _execute_post_opportunity_steps(
        sf=sf,
        sf_is_sandbox=sf_is_sandbox,
        opportunity_id=opportunity_id,
        account_id=convert_res.get("account_id"),
        contact_id=contact_id,
        advisor_salesforce_id=advisor_salesforce_id,
        advisor_name=advisor_name,
        sdr_salesforce_id=sdr_salesforce_id,
        sdr_name=sdr_name,
        sdr_email=sdr_email,
        client_name=lead_name,
        patrimony_value=patrimony_value,
        profissao=profissao,
        interesse_investimentos=interesse_investimentos,
        description=description,
        event_datetime=event_datetime,
        duration_minutes=duration_minutes,
        modalidade=modalidade,
        is_consorcio=is_consorcio,
        opportunity_type="consorcio" if is_consorcio else "lead",
        flow_result=flow_result,
        steps_completed=steps_completed,
        errors=errors,
    )

    # ─── Final ───
    # Converting the Lead is not the deliverable: an R1 only exists when the
    # advisor owns the records, the Event is on the calendar and the Opp moved
    # stage. Same critical set execute_r1_finalize_flow already gates on.
    flow_result["success"] = R1_CRITICAL_STEPS.issubset(set(steps_completed))
    logger.info(
        "R1 FLOW %s — steps: %s | errors: %s",
        "COMPLETED" if flow_result["success"] else "FAILED",
        steps_completed, errors,
    )
    return flow_result


def execute_r1_resume_converted_lead_flow(
    *,
    lead_id: str,
    opportunity_id: str,
    account_id: str,
    contact_id: Optional[str],
    lead_name: str,
    patrimony_value: float,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    event_datetime: datetime,
    advisor_salesforce_id: str,
    advisor_name: str,
    sdr_salesforce_id: str,
    sdr_name: str,
    sdr_email: Optional[str] = None,
    is_consorcio: bool = False,
    duration_minutes: int = MEETING_DURATION,
    modalidade: str = "Online",
) -> Dict[str, Any]:
    """Resume the post-conversion half of a failed synchronous Super R1.

    Salesforce lead conversion commits before the remaining API writes. A retry
    must target the original ConvertedOpportunityId; creating or converting
    again would duplicate the client funnel and possibly the calendar event.
    """
    sf_is_sandbox = os.getenv("SF_IS_SANDBOX", "false").lower() in ("true", "1", "yes")
    steps_completed: List[str] = ["lead_already_converted"]
    errors: List[str] = []
    result: Dict[str, Any] = {
        "success": False,
        "lead_id": _validate_sf_id(lead_id),
        "account_id": _validate_sf_id(account_id),
        "contact_id": _validate_sf_id(contact_id) if contact_id else None,
        "opportunity_id": _validate_sf_id(opportunity_id),
        "event_id": None,
        "steps_completed": steps_completed,
        "errors": errors,
        "sandbox_mode": sf_is_sandbox,
    }
    sf = get_salesforce_connection()
    if not sf:
        errors.append("Falha na autenticação com Salesforce")
        return result

    # A retry may reuse an Event only for the same requested slot. A later,
    # genuinely new scheduling attempt through the old Lead id must not append
    # a second R1 to the already-converted Opportunity; callers should use the
    # Account route to create a new Opportunity instead.
    #
    # The decision is "does an R1 for THIS slot exist", so every R1 on the
    # Opportunity is weighed, not just the newest one: an Opportunity left in a
    # strange state by an interrupted conversion can carry an R1 at the
    # requested slot AND a newer one elsewhere, and picking by CreatedDate
    # would reject the retry that the matching Event proves is legitimate.
    # An unparseable StartDateTime (null, or naive) can only mean "not this
    # slot" — it must not raise, or the recovery answers 500 instead of the
    # typed error below.
    requested_start = event_datetime.astimezone(timezone.utc)
    existing_events = sf.query(
        "SELECT Id, StartDateTime FROM Event "
        f"WHERE WhatId = '{result['opportunity_id']}' AND Type = 'R1' "
        "ORDER BY CreatedDate DESC LIMIT 200"
    )
    existing_rows = existing_events.get("records") or []

    def _starts_at_requested_slot(row: Dict[str, Any]) -> bool:
        try:
            return _parse_sf_datetime(row.get("StartDateTime")) == requested_start
        except (ValueError, TypeError):
            return False

    if existing_rows and not any(_starts_at_requested_slot(r) for r in existing_rows):
        errors.append(
            "Lead já convertido possui R1 em outro horário; use a Account "
            "para criar uma nova Opportunity."
        )
        result["event_id"] = existing_rows[0].get("Id")
        return result

    _execute_post_opportunity_steps(
        sf=sf,
        sf_is_sandbox=sf_is_sandbox,
        opportunity_id=result["opportunity_id"],
        account_id=result["account_id"],
        contact_id=result["contact_id"],
        advisor_salesforce_id=advisor_salesforce_id,
        advisor_name=advisor_name,
        sdr_salesforce_id=sdr_salesforce_id,
        sdr_name=sdr_name,
        sdr_email=sdr_email,
        client_name=lead_name,
        patrimony_value=patrimony_value,
        profissao=profissao,
        interesse_investimentos=interesse_investimentos,
        description=description,
        event_datetime=event_datetime,
        duration_minutes=duration_minutes,
        modalidade=modalidade,
        is_consorcio=is_consorcio,
        opportunity_type="consorcio" if is_consorcio else "lead",
        flow_result=result,
        steps_completed=steps_completed,
        errors=errors,
        resuming_converted_lead=True,
    )
    result["success"] = R1_CRITICAL_STEPS.issubset(set(steps_completed))
    return result


# =============================================================================
# D+1 SPLIT FLOWS (partial at submission, finalize at 22:00 BRT)
# =============================================================================


def execute_r1_partial_flow_lead(
    lead_id: str,
    lead_name: str,
    lead_email: Optional[str],
    patrimony_value: float,
    patrimony_range: str,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    sdr_salesforce_id: str,
    sdr_name: str,
    sdr_email: Optional[str],
    placeholder_owner_id: str,  # SDR SF User Id — temporary owner until 22h batch assigns the real advisor
    lead_source: Optional[str] = None,
    sf_user_connection: Optional[Salesforce] = None,
    # Consórcio fields — always None for D+1 (consórcio doesn't use this flow)
    idade: Optional[int] = None,
    modalidade_calculo: Optional[str] = None,
    id_carta: Optional[int] = None,
    tomador_decisao: Optional[str] = None,
    intuito_consorcio: Optional[str] = None,
    interesses_consorcios: Optional[str] = None,
) -> Dict[str, Any]:
    """
    D+1 SUBMISSION — partial R1 flow for LEADS (SYNCHRONOUS).

    Does everything that does NOT depend on knowing the final advisor:
      1. Update Lead fields
      2. Convert Lead → Opportunity (owner = placeholder_owner_id)
      3. Populate Opportunity with SDR fields (patrimony, profissao, etc.)
      4. Add SDR as OpportunityTeamMember

    Does NOT:
      - Transfer Account/Contact ownership (no advisor yet)
      - Create R1 Event (no advisor calendar)
      - Advance Opportunity stage (would fail validation rule)
      - Write routing_history / notification

    Returns: {
        success, opportunity_id, contact_id, account_id,
        steps_completed, errors, sandbox_mode
    }

    The caller stores opportunity_id/contact_id/account_id in the pending
    row so the 22:00 batch can finalize via execute_r1_finalize_flow.
    """
    sf_is_sandbox = os.getenv("SF_IS_SANDBOX", "false").lower() in ("true", "1", "yes")
    logger.info(
        "┌─ D+1 PARTIAL (Lead) — %s ─",
        "SANDBOX" if sf_is_sandbox else "PRODUCTION",
    )
    logger.info("│  Lead: %s (%s), patrimony: %s", lead_id, lead_name, patrimony_value)
    logger.info("│  Routing Queue User (temp owner): %s", placeholder_owner_id)

    steps_completed: List[str] = []
    errors: List[str] = []
    flow_result: Dict[str, Any] = {
        "success": False,
        "lead_id": lead_id,
        "opportunity_id": None,
        "contact_id": None,
        "account_id": None,
        "steps_completed": steps_completed,
        "errors": errors,
        "sandbox_mode": sf_is_sandbox,
    }

    sf = get_salesforce_connection()
    if not sf:
        errors.append("Falha na autenticação com Salesforce")
        return flow_result
    steps_completed.append("salesforce_connected")

    sf_write = resolve_write_connection(sf, sf_user_connection, sdr_email)

    # STEP 0.5: Resolve sandbox lead ID
    actual_lead_id = lead_id
    if sf_is_sandbox:
        sandbox_id = resolve_sandbox_lead_id(sf, lead_email, lead_name)
        if sandbox_id:
            actual_lead_id = sandbox_id
            flow_result["sandbox_lead_id"] = sandbox_id
        else:
            errors.append(f"Lead não encontrado no Sandbox (email={lead_email}, nome={lead_name})")
            return flow_result

    # STEP 1: Update Lead fields
    try:
        upd = update_lead_fields(
            sf=sf_write, lead_id=actual_lead_id,
            patrimony_value=patrimony_value, patrimony_range=patrimony_range,
            profissao=profissao, interesse_investimentos=interesse_investimentos,
            description=description, is_consorcio=False,
            idade=idade, modalidade_calculo=modalidade_calculo, id_carta=id_carta,
            tomador_decisao=tomador_decisao, intuito_consorcio=intuito_consorcio,
            interesses_consorcios=interesses_consorcios,
        )
        if upd.get("success"):
            steps_completed.append("lead_updated")
        else:
            errors.append(f"Falha ao atualizar Lead: {upd.get('message')}")
    except Exception as e:
        errors.append(f"Erro ao atualizar Lead: {e}")
        logger.error("D+1 partial STEP 1 error: %s", e, exc_info=True)

    # STEP 2: Convert Lead → Opp (owner = Routing Queue User, NOT the SDR)
    try:
        conv = convert_lead_to_opportunity(
            sf=sf_write, lead_id=actual_lead_id,
            sdr_user_id=placeholder_owner_id,  # temp placeholder owner
            lead_name=lead_name, lead_source=lead_source,
        )
        if not conv.get("success"):
            errors.append(f"Falha na conversão do Lead: {conv.get('message')}")
            return flow_result
        opportunity_id = _validate_sf_id(conv["opportunity_id"])
        contact_id = conv.get("contact_id")
        account_id = conv.get("account_id")
        flow_result["opportunity_id"] = opportunity_id
        flow_result["contact_id"] = contact_id
        flow_result["account_id"] = account_id
        steps_completed.append("lead_converted")
        logger.info("│  Lead converted: Opp=%s Contact=%s Account=%s", opportunity_id, contact_id, account_id)
    except Exception as e:
        errors.append(f"Erro na conversão do Lead: {e}")
        logger.error("D+1 partial STEP 2 error: %s", e, exc_info=True)
        return flow_result

    # STEP 3: Populate SDR-informed fields on Opp (NO owner change, NO stage advance)
    # Fields that don't require advisor knowledge.
    partial_opp_data: Dict[str, Any] = {
        "DWPatrimonioFinanceiroInformado__c": patrimony_value,
        "DWValorInformadoPeloSDR__c": patrimony_value,
        "DWNomeSDR__c": sdr_name,
        "DWDescricaoOportunidade__c": "",
        "DWProfissao__c": profissao,
        "DWInteressesInvestimento__c": interesse_investimentos,
    }
    # FBI-2925: stamp Investimentos vs Financial Services on D+1 submit
    # (batch finalize does not set RecordType today).
    try:
        from app.services.super_r1_service import (
            opportunity_funnel,
            patrimony_to_categoria,
        )
        funnel = opportunity_funnel(patrimony_to_categoria(patrimony_value))
        rt_id = _resolve_opportunity_record_type_id(sf, funnel) if funnel else None
        if rt_id:
            partial_opp_data["RecordTypeId"] = rt_id
            logger.info(
                "D+1 partial (Lead): Opp RecordType funnel=%s id=%s",
                funnel,
                rt_id,
            )
    except Exception as e:
        logger.warning("D+1 partial (Lead): could not resolve Opp RecordType: %s", e)
    partial_opp_data = {k: v for k, v in partial_opp_data.items() if v is not None}
    try:
        sf.Opportunity.update(opportunity_id, partial_opp_data)  # type: ignore
        steps_completed.append("opportunity_partial_update")
    except Exception as e:
        errors.append(f"Erro ao atualizar Opp (partial): {e}")
        logger.error("D+1 partial STEP 3 error: %s", e, exc_info=True)

    # STEP 4: Fix SDR OpportunityTeamMember
    real_sdr_sf_id = _resolve_active_user_id_by_email(sf, sdr_email) if sdr_email else None
    if real_sdr_sf_id:
        try:
            _ensure_sdr_team_member(
                sf,
                opportunity_id=opportunity_id,
                real_sdr_sf_id=real_sdr_sf_id,
                sdr_email=sdr_email,
                advisor_salesforce_id=None,
                steps_completed=steps_completed,
                errors=errors,
            )
        except Exception as e:
            errors.append(f"Erro em SDR team member: {e}")

    flow_result["success"] = "lead_converted" in steps_completed
    logger.info(
        "│  PARTIAL DONE — success=%s steps=%s",
        flow_result["success"], steps_completed,
    )
    return flow_result


def execute_above_10m_conversion_flow(
    *,
    lead_id: str,
    lead_name: str,
    lead_email: Optional[str],
    lead_source: Optional[str],
    patrimony_value: float,
    patrimony_range: str,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    daniel_salesforce_id: str,
    daniel_name: str,
    sdr_salesforce_id: str,
    sdr_name: str,
    sdr_email: Optional[str],
    sf_user_connection: Optional[Salesforce] = None,
) -> Dict[str, Any]:
    """
    Above-10M qualification flow (synchronous).

    Lead is fully converted; the resulting Opportunity, Contact and Account
    are owned by Daniel da AMB. SDR is added to the Opportunity team with
    role 'SDR'. No Event is created and no Opportunity stage advance happens
    — AMB handles the meeting internally.

    routing_history is recorded (so analytics see the qualification);
    routing_notification is intentionally skipped (Daniel is not in the
    advisor round-robin).
    """
    sf_is_sandbox = os.getenv("SF_IS_SANDBOX", "false").lower() in ("true", "1", "yes")
    logger.info("┌─ ABOVE-10M CONVERSION — %s", "SANDBOX" if sf_is_sandbox else "PRODUCTION")
    logger.info("│  Lead: %s (%s), patrimony: %s", lead_id, lead_name, patrimony_value)
    logger.info("│  Target owner: %s (%s)", daniel_name, daniel_salesforce_id)

    steps_completed: List[str] = []
    errors: List[str] = []
    flow_result: Dict[str, Any] = {
        "success": False,
        "lead_id": lead_id,
        "opportunity_id": None,
        "contact_id": None,
        "account_id": None,
        "steps_completed": steps_completed,
        "errors": errors,
        "sandbox_mode": sf_is_sandbox,
    }

    sf = get_salesforce_connection()
    if not sf:
        errors.append("Falha na autenticação com Salesforce")
        return flow_result
    steps_completed.append("salesforce_connected")

    sf_write = resolve_write_connection(sf, sf_user_connection, sdr_email)

    actual_lead_id = lead_id
    if sf_is_sandbox:
        sandbox_id = resolve_sandbox_lead_id(sf, lead_email, lead_name)
        if sandbox_id:
            actual_lead_id = sandbox_id
            flow_result["sandbox_lead_id"] = sandbox_id
        else:
            errors.append(f"Lead não encontrado no Sandbox (email={lead_email}, nome={lead_name})")
            return flow_result

    try:
        upd = update_lead_fields(
            sf=sf_write, lead_id=actual_lead_id,
            patrimony_value=patrimony_value, patrimony_range=patrimony_range,
            profissao=profissao, interesse_investimentos=interesse_investimentos,
            description=description, is_consorcio=False,
        )
        if upd.get("success"):
            steps_completed.append("lead_updated")
        else:
            errors.append(f"Falha ao atualizar Lead: {upd.get('message')}")
    except Exception as e:
        errors.append(f"Erro ao atualizar Lead: {e}")
        return flow_result

    try:
        conv = convert_lead_to_opportunity(
            sf=sf_write,
            lead_id=actual_lead_id,
            sdr_user_id=daniel_salesforce_id,
            lead_name=lead_name,
            lead_source=lead_source,
        )
        if not conv.get("success"):
            errors.append(f"Falha na conversão do Lead: {conv.get('message')}")
            return flow_result

        opportunity_id = conv.get("opportunity_id")
        contact_id = conv.get("contact_id")
        account_id = conv.get("account_id")
        flow_result["opportunity_id"] = opportunity_id
        flow_result["contact_id"] = contact_id
        flow_result["account_id"] = account_id
        steps_completed.append("lead_converted")
    except Exception as e:
        errors.append(f"Erro na conversão do Lead: {e}")
        return flow_result

    if opportunity_id:
        try:
            current_opp = sf.Opportunity.get(opportunity_id)
            current_owner = current_opp.get("OwnerId") if isinstance(current_opp, dict) else None
            if current_owner != daniel_salesforce_id:
                logger.warning(
                    "POST-CONVERT[opp=%s]: OwnerId=%s != Daniel(%s) — forcing update",
                    opportunity_id, current_owner, daniel_salesforce_id,
                )
                sf.Opportunity.update(opportunity_id, {"OwnerId": daniel_salesforce_id})
                steps_completed.append("opp_owner_forced_to_daniel")
            else:
                steps_completed.append("opp_owner_correct")
        except Exception as e:
            errors.append(f"Erro ao forçar OwnerId da Opp para Daniel: {e}")

    real_sdr_sf_id = _resolve_active_user_id_by_email(sf, sdr_email) if sdr_email else None
    if real_sdr_sf_id:
        try:
            _ensure_sdr_team_member(
                sf,
                opportunity_id=opportunity_id,
                real_sdr_sf_id=real_sdr_sf_id,
                sdr_email=sdr_email,
                advisor_salesforce_id=daniel_salesforce_id,
                steps_completed=steps_completed,
                errors=errors,
            )
        except Exception as e:
            errors.append(f"Erro ao garantir SDR team member: {e}")
    else:
        logger.warning(
            "POST-OPP[opp=%s]: SDR (%s / %s) not resolved as active SF User — skipping SDR team member",
            opportunity_id, sdr_name, sdr_email,
        )

    try:
        own = update_ownership_after_conversion(
            sf=sf, account_id=account_id, contact_id=contact_id,
            advisor_salesforce_id=daniel_salesforce_id, advisor_name=daniel_name,
        )
        if own.get("success"):
            steps_completed.append("ownership_transferred")
        else:
            errors.append(
                f"Falha parcial na transferência de propriedade: "
                f"Account={own.get('account_error', 'OK')}, "
                f"Contact={own.get('contact_error', 'OK')}"
            )
    except Exception as e:
        errors.append(f"Erro na transferência de propriedade: {e}")

    if opportunity_id:
        try:
            rh_ok = insert_routing_history(
                opportunity_id=opportunity_id,
                advisor_salesforce_id=daniel_salesforce_id,
                patrimony_value=patrimony_value,
                opportunity_type="lead",
            )
            if rh_ok:
                steps_completed.append("routing_history_inserted")
            else:
                errors.append("routing_history not inserted (no row)")
        except Exception as e:
            errors.append(f"Erro routing_history: {e}")

    flow_result["success"] = "lead_converted" in steps_completed and "ownership_transferred" in steps_completed
    logger.info(
        "│  ABOVE-10M DONE — success=%s steps=%s errors=%s",
        flow_result["success"], steps_completed, errors,
    )
    return flow_result


def execute_r1_partial_flow_from_account(
    account_id: str,
    contact_id: Optional[str],
    client_name: str,
    patrimony_value: float,
    patrimony_range: str,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    sdr_salesforce_id: str,
    sdr_name: str,
    sdr_email: Optional[str],
    placeholder_owner_id: str,
    lead_source: Optional[str] = None,
    sf_user_connection: Optional[Salesforce] = None,
) -> Dict[str, Any]:
    """
    D+1 SUBMISSION — partial R1 flow for ACCOUNTS (SYNCHRONOUS).

    Matches Lead-D+1 semantics for an Account-only path: new Opportunity,
    Account, and Contact ownership all go to the placeholder. No Event is
    created here — the 21:00 BRT batch creates it on the picked advisor's
    calendar (same path the Lead-D+1 flow uses). Adds SDR as TeamMember.
    """
    sf_is_sandbox = os.getenv("SF_IS_SANDBOX", "false").lower() in ("true", "1", "yes")
    logger.info(
        "┌─ D+1 PARTIAL (Account) — %s ─",
        "SANDBOX" if sf_is_sandbox else "PRODUCTION",
    )

    steps_completed: List[str] = []
    errors: List[str] = []
    flow_result: Dict[str, Any] = {
        "success": False,
        "opportunity_id": None,
        "contact_id": contact_id,
        "account_id": account_id,
        "steps_completed": steps_completed,
        "errors": errors,
        "sandbox_mode": sf_is_sandbox,
    }

    sf = get_salesforce_connection()
    if not sf:
        errors.append("Falha na autenticação com Salesforce")
        return flow_result

    sf_write = resolve_write_connection(sf, sf_user_connection, sdr_email)

    # STEP 1: Create new Opportunity (owner = Routing Queue User)
    opp_name = f"{client_name} - {lead_source}" if lead_source else client_name
    close_date = (date.today() + timedelta(days=90)).isoformat()

    # FBI-3061 (D4=Opção C): mitigação causalmente agnóstica — quando o STEP 1
    # nega o create sob a sessão do operador com um errorCode de acesso
    # reconhecido (SF_USER_FALLBACK_ERROR_CODES), retenta o MESMO payload sob
    # a conexão admin. A causa da negação segue em aberto (ver
    # tasks/sprint-16/FBI-3061-evidencia.md); isto não corrige mecanismo
    # conhecido, só evita que o SDR fique bloqueado enquanto a causa não
    # fecha. Laço sobre conexões (não 2 chamadas literais) para que
    # `grep -c 'Opportunity\.create('` continue contando 2 no arquivo — uma
    # segunda chamada explícita quebraria essa prova de "só os 2 sítios
    # nomeados" (§9 do plano, R2/R9). A construção do payload (inclusive os
    # `_validate_sf_id`) fica DENTRO do try — um id malformado cai no mesmo
    # caminho de erro gracioso de sempre, não escapa cru.
    create_result: Optional[Dict[str, Any]] = None
    create_error_texts: List[str] = []
    used_admin_fallback = False
    for attempt_idx, conn in enumerate((sf_write, sf)):
        try:
            opp_payload = {
                "Name": opp_name,
                "AccountId": _validate_sf_id(account_id),
                "StageName": "Nova oportunidade",
                "OwnerId": _validate_sf_id(placeholder_owner_id),
                "CloseDate": close_date,
            }
            create_result = conn.Opportunity.create(opp_payload)  # type: ignore
            used_admin_fallback = attempt_idx == 1
            break
        except Exception as e:
            create_error_texts.append(str(e))
            create_result = None
            if conn is sf or not is_sf_user_access_error(e):
                break

    if create_result is None:
        errors.append(f"Erro ao criar Opp: {create_error_texts[0]}")
        if len(create_error_texts) > 1:
            errors.append(
                f"Fallback admin também negado ao criar Opp: {create_error_texts[1]}"
            )
        return flow_result

    if not create_result.get("success"):
        errs = create_result.get("errors", [])
        errors.append(f"Falha ao criar Opp: {errs}")
        return flow_result
    opportunity_id = _validate_sf_id(create_result["id"])
    flow_result["opportunity_id"] = opportunity_id
    steps_completed.append("opportunity_created")
    if used_admin_fallback:
        steps_completed.append("opportunity_created_admin_fallback")

    # STEP 2: Partial Opp update (fields that don't need advisor)
    partial_opp_data: Dict[str, Any] = {
        "DWPatrimonioFinanceiroInformado__c": patrimony_value,
        "DWValorInformadoPeloSDR__c": patrimony_value,
        "DWNomeSDR__c": sdr_name,
        "DWDescricaoOportunidade__c": "",
        "DWProfissao__c": profissao,
        "DWInteressesInvestimento__c": interesse_investimentos,
    }
    # FBI-2925: stamp Investimentos vs Financial Services on D+1 submit
    try:
        from app.services.super_r1_service import (
            opportunity_funnel,
            patrimony_to_categoria,
        )
        funnel = opportunity_funnel(patrimony_to_categoria(patrimony_value))
        rt_id = _resolve_opportunity_record_type_id(sf, funnel) if funnel else None
        if rt_id:
            partial_opp_data["RecordTypeId"] = rt_id
            logger.info(
                "D+1 partial (Account): Opp RecordType funnel=%s id=%s",
                funnel,
                rt_id,
            )
    except Exception as e:
        logger.warning("D+1 partial (Account): could not resolve Opp RecordType: %s", e)
    partial_opp_data = {k: v for k, v in partial_opp_data.items() if v is not None}
    try:
        sf.Opportunity.update(opportunity_id, partial_opp_data)  # type: ignore
        steps_completed.append("opportunity_partial_update")
    except Exception as e:
        errors.append(f"Erro ao atualizar Opp (partial): {e}")

    # STEP 3: SDR TeamMember (uses shared helper to handle SF auto-creation conflicts)
    real_sdr_sf_id = _resolve_active_user_id_by_email(sf, sdr_email) if sdr_email else None
    if real_sdr_sf_id:
        try:
            _ensure_sdr_team_member(
                sf,
                opportunity_id=opportunity_id,
                real_sdr_sf_id=real_sdr_sf_id,
                sdr_email=sdr_email,
                advisor_salesforce_id=None,
                steps_completed=steps_completed,
                errors=errors,
            )
        except Exception as e:
            errors.append(f"Erro em SDR team member: {e}")

    # STEP 4: Transfer Account ownership to placeholder
    try:
        sf_write.Account.update(_validate_sf_id(account_id), {  # type: ignore
            "OwnerId": _validate_sf_id(placeholder_owner_id),
        })
        steps_completed.append("account_owner_to_placeholder")
    except Exception as e:
        errors.append(f"Erro ao transferir Account para placeholder: {e}")

    # STEP 5: Transfer Contact ownership to placeholder
    if contact_id:
        try:
            sf_write.Contact.update(_validate_sf_id(contact_id), {  # type: ignore
                "OwnerId": _validate_sf_id(placeholder_owner_id),
            })
            steps_completed.append("contact_owner_to_placeholder")
        except Exception as e:
            errors.append(f"Erro ao transferir Contact para placeholder: {e}")

    flow_result["success"] = "opportunity_created" in steps_completed
    logger.info("│  PARTIAL (account) DONE — success=%s", flow_result["success"])
    return flow_result


def execute_r1_finalize_flow(
    *,
    opportunity_id: str,
    account_id: Optional[str],
    contact_id: Optional[str],
    advisor_salesforce_id: str,
    advisor_name: str,
    client_name: str,
    patrimony_value: float,
    interesse_investimentos: str,
    description: str,
    event_datetime: datetime,
    duration_minutes: int = MEETING_DURATION,
    modalidade: str = "Online",
    is_consorcio: bool = False,
    opportunity_type: str = "lead",
) -> Dict[str, Any]:
    """
    D+1 22:00 BATCH — finalize a previously-created D+1 Opportunity.

    Steps:
      1. Transfer Account & Contact ownership to advisor
      2. Create R1 Event (advisor's calendar)
      3. Update Opportunity: OwnerId + StageName("Contatado") + DWStatusReunioesInvestimentos__c
      4. Insert routing_history
      5. Insert routing_notification (non-sandbox only)

    Assumes steps that happened at submission (Lead update, convertLead,
    SDR fields on Opp, SDR TeamMember) are already done.
    """
    sf_is_sandbox = os.getenv("SF_IS_SANDBOX", "false").lower() in ("true", "1", "yes")
    logger.info(
        "┌─ D+1 FINALIZE — opp=%s advisor=%s (%s)",
        opportunity_id, advisor_salesforce_id, advisor_name,
    )

    steps_completed: List[str] = []
    errors: List[str] = []
    result: Dict[str, Any] = {
        "success": False,
        "opportunity_id": opportunity_id,
        "contact_id": contact_id,
        "event_id": None,
        "event_write_outcome": "event_not_attempted",
        "steps_completed": steps_completed,
        "errors": errors,
        "sandbox_mode": sf_is_sandbox,
    }

    sf = get_salesforce_connection()
    if not sf:
        errors.append("Falha na autenticação com Salesforce")
        return result

    # 1. Transfer ownership
    try:
        own = update_ownership_after_conversion(
            sf=sf, account_id=account_id, contact_id=contact_id,
            advisor_salesforce_id=advisor_salesforce_id, advisor_name=advisor_name,
        )
        if own.get("success"):
            steps_completed.append("ownership_transferred")
        else:
            errors.append(f"Falha parcial ownership: {own}")
    except Exception as e:
        errors.append(f"Erro ownership: {e}")

    # 2. Create R1 Event (on advisor's calendar, NOT the routing queue user's)
    try:
        evt = create_r1_event(
            sf=sf, opportunity_id=opportunity_id, contact_id=contact_id,
            advisor_salesforce_id=advisor_salesforce_id,
            event_datetime=event_datetime, description=description,
            duration_minutes=duration_minutes, modalidade=modalidade,
        )
        if evt.get("success"):
            result["event_id"] = evt["event_id"]
            steps_completed.append("event_created")
        else:
            errors.append(f"Falha Event: {evt.get('message')}")
    except Exception as e:
        errors.append(f"Erro Event: {e}")

    # 3. Update Opp: owner + stage advance + status
    # Only the fields that need the advisor / event. Other fields (patrimony,
    # SDR name, etc.) were set at submission.
    opp_update_data: Dict[str, Any] = {
        "OwnerId": advisor_salesforce_id,
        "StageName": "Apresentação da Estratégia" if is_consorcio else "Contatado",
        "DWStatusReunioesInvestimentos__c": "R1 Agendada em aberto",
    }
    if is_consorcio:
        opp_update_data["DWEspecialistaResponsavel__c"] = advisor_salesforce_id
    try:
        sf.Opportunity.update(opportunity_id, opp_update_data)  # type: ignore
        steps_completed.append("opportunity_updated")
    except Exception as e:
        errors.append(f"Erro Opp update: {e}")
        logger.error("D+1 finalize: Opp update failed: %s", e, exc_info=True)

    # 4. routing_history
    try:
        rh_ok = insert_routing_history(
            opportunity_id=opportunity_id,
            advisor_salesforce_id=advisor_salesforce_id,
            patrimony_value=patrimony_value,
            opportunity_type=opportunity_type,
        )
        if rh_ok:
            steps_completed.append("routing_history_inserted")
        else:
            errors.append("routing_history not inserted")
    except Exception as e:
        errors.append(f"Erro routing_history: {e}")

    # 5. routing_notification (non-sandbox only)
    if not sf_is_sandbox:
        try:
            from datetime import timezone
            n_ok = insert_routing_notification(
                opportunity_id=opportunity_id,
                advisor_salesforce_id=advisor_salesforce_id,
                client_name=client_name,
                patrimony_value=patrimony_value,
                routed_at=datetime.now(timezone.utc).isoformat(),
                description=description,
                investment_interests=interesse_investimentos,
            )
            if n_ok:
                steps_completed.append("routing_notification_inserted")
        except Exception as e:
            errors.append(f"Erro routing_notification: {e}")
    else:
        steps_completed.append("routing_notification_skipped_sandbox")

    # Success = all critical steps done (ownership + event + opp_update + history)
    result["success"] = R1_FINALIZE_CRITICAL_STEPS.issubset(set(steps_completed))
    logger.info(
        "│  FINALIZE DONE — success=%s steps=%s errors=%s",
        result["success"], steps_completed, errors,
    )
    return result


# =============================================================================
# R1 SCHEDULING FROM EXISTING OPPORTUNITY
# =============================================================================


def execute_r1_from_opportunity_flow(
    source_opp_id: Optional[str],
    account_id: str,
    contact_id: Optional[str],
    client_name: str,
    patrimony_value: float,
    patrimony_range: str,
    profissao: str,
    interesse_investimentos: str,
    description: str,
    event_datetime: datetime,
    advisor_salesforce_id: str,
    advisor_name: str,
    sdr_salesforce_id: str,
    sdr_name: str,
    sdr_email: Optional[str] = None,
    lead_source: Optional[str] = None,
    duration_minutes: int = MEETING_DURATION,
    modalidade: str = "Online",
    sf_user_connection: Optional[Salesforce] = None,
    is_consorcio: bool = False,
    # Consórcio-specific fields (for writing to Opportunity)
    idade: Optional[int] = None,
    modalidade_calculo: Optional[str] = None,
    id_carta: Optional[int] = None,
    tomador_decisao: Optional[str] = None,
    intuito_consorcio: Optional[str] = None,
    interesses_consorcios: Optional[str] = None,
    # Estado da OPP de entrada antes da R1 (só com source_opp_id).
    source_opp_state: Optional[ReusedOpportunityState] = None,
) -> Dict[str, Any]:
    """
    Execute the R1 scheduling flow from an existing Opportunity (SYNCHRONOUS).

    Instead of converting a Lead, creates a NEW Opportunity linked to the same
    Account/Contact and performs the remaining steps on it.

    With `source_opp_id` (FBI-4719, entrada por OPP existente) the creation step
    is skipped: that Opportunity is reused and gets the same Event, owner and
    field updates as a new one. Without it the flow creates, as before.

    Must be called via run_in_executor from async context.
    """
    sf_is_sandbox = os.getenv("SF_IS_SANDBOX", "false").lower() in ("true", "1", "yes")

    logger.info(
        "╔══════════════════════════════════════════════════════════════╗"
    )
    logger.info(
        "║  R1 FROM OPP FLOW — %s",
        "SANDBOX MODE" if sf_is_sandbox else "PRODUCTION MODE",
    )
    logger.info(
        "╠══════════════════════════════════════════════════════════════╣"
    )
    logger.info("║  Source Opp ID:     %s", source_opp_id)
    logger.info("║  Account ID:        %s", account_id)
    logger.info("║  Contact ID:        %s", contact_id)
    logger.info("║  Client Name:       %s", client_name)
    logger.info("║  Patrimony:         %s (%s)", patrimony_value, patrimony_range)
    logger.info("║  Profissão:         %s", profissao)
    logger.info("║  Interesses:        %s", interesse_investimentos)
    logger.info("║  Description:       %s", description[:80] if description else "N/A")
    logger.info("║  Event:             %s (%d min, %s)", event_datetime, duration_minutes, modalidade)
    logger.info("║  Advisor SF ID:     %s (%s)", advisor_salesforce_id, advisor_name)
    logger.info("║  SDR SF ID:         %s (%s)", sdr_salesforce_id, sdr_name)
    logger.info(
        "╚══════════════════════════════════════════════════════════════╝"
    )

    steps_completed: List[str] = []
    errors: List[str] = []
    flow_result: Dict[str, Any] = {
        "success": False,
        "source_account_id": account_id,
        "opportunity_id": None,
        "contact_id": contact_id,
        "event_id": None,
        "event_write_outcome": "event_not_attempted",
        "steps_completed": steps_completed,
        "errors": errors,
        "sandbox_mode": sf_is_sandbox,
    }

    # ─── STEP 0: Connect ───
    sf = get_salesforce_connection()
    if not sf:
        errors.append("Falha na autenticação com Salesforce")
        notify_teams_salesforce_error(
            "Falha na autenticação com Salesforce",
            operation="R1 from Opp Scheduling",
        )
        return flow_result
    steps_completed.append("salesforce_connected")

    sf_write = resolve_write_connection(sf, sf_user_connection, sdr_email)
    if sf_user_connection:
        logger.info(
            "STEP 0: Connected — admin=%s, writes-as-user=%s (JWT per-user auth active)",
            sf.sf_instance, sf_user_connection.sf_instance,
        )
        steps_completed.append("jwt_per_user_auth")
    else:
        logger.info(
            "STEP 0: Connected to Salesforce (%s) — writes use admin account",
            sf.sf_instance,
        )

    # ─── STEP 1: Opportunity — reaproveita a de entrada ou cria uma nova ───
    # FBI-4719: a entrada por OPP existente roda o mesmo pacote do caminho
    # Conta (evento, roteamento, dono e campos), sem a criação. A validação do
    # id usa o mesmo retorno gracioso do create, então um id malformado vira
    # erro no flow_result e não exceção crua.
    reused_opportunity = bool(source_opp_id)
    if source_opp_id:
        try:
            opportunity_id = _validate_sf_id(source_opp_id)
        except Exception as e:
            errors.append(f"Opportunity de entrada inválida: {e}")
            logger.error("STEP 1 (reuse opportunity) invalid id %r: %s", source_opp_id, e)
            return flow_result
        flow_result["opportunity_id"] = opportunity_id
        steps_completed.append("opportunity_reused")
        logger.info(
            "STEP 1: Reusing existing Opportunity %s (Account=%s) — no create",
            opportunity_id, account_id,
        )
    else:
        opp_name = f"{client_name} - {lead_source}" if lead_source else client_name
        close_date = (date.today() + timedelta(days=90)).isoformat()

        logger.info("STEP 1: Creating new Opportunity for Account %s...", account_id)

        # FBI-3061 (D4=Opção C) — mesmo contrato do site D+1 acima: fallback
        # user→admin com o MESMO payload quando o errorCode é reconhecido como
        # negação de sessão do operador. Mitigação causalmente agnóstica, causa
        # em aberto (ver tasks/sprint-16/FBI-3061-evidencia.md). Laço sobre
        # conexões, não 2a chamada literal — preserva `grep -c
        # 'Opportunity\.create('` == 2 no arquivo. A construção do payload
        # (inclusive os `_validate_sf_id`) fica DENTRO do try — um id malformado
        # tem de cair no mesmo caminho de erro gracioso de sempre, não escapar
        # cru (regressão que a Tarefa 9 quase introduziu: mover a validação para
        # fora do try faria um ID inválido virar exceção não tratada).
        create_result: Optional[Dict[str, Any]] = None
        create_error_texts: List[str] = []
        used_admin_fallback = False
        for attempt_idx, conn in enumerate((sf_write, sf)):
            try:
                new_opp_data = {
                    "Name": opp_name,
                    "AccountId": _validate_sf_id(account_id),
                    "StageName": "Nova oportunidade",
                    "OwnerId": _validate_sf_id(sdr_salesforce_id),
                    "CloseDate": close_date,
                }
                create_result = conn.Opportunity.create(new_opp_data)  # type: ignore
                used_admin_fallback = attempt_idx == 1
                break
            except Exception as e:
                create_error_texts.append(str(e))
                create_result = None
                if conn is sf or not is_sf_user_access_error(e):
                    break

        if create_result is None:
            errors.append(f"Erro ao criar Opportunity: {create_error_texts[0]}")
            logger.error("STEP 1 (create opportunity) error: %s", create_error_texts[0])
            if len(create_error_texts) > 1:
                errors.append(
                    f"Fallback admin também negado ao criar Opportunity: {create_error_texts[1]}"
                )
                logger.error(
                    "STEP 1 (create opportunity) admin fallback also denied: %s",
                    create_error_texts[1],
                )
            return flow_result

        if not create_result.get("success"):
            opp_errors = create_result.get("errors", [])
            error_msg = "; ".join(str(e) for e in opp_errors) if opp_errors else "Erro desconhecido"
            errors.append(f"Falha ao criar Opportunity: {error_msg}")
            logger.error("STEP 1: Failed to create Opportunity: %s", error_msg)
            return flow_result

        opportunity_id = _validate_sf_id(create_result["id"])
        flow_result["opportunity_id"] = opportunity_id
        steps_completed.append("opportunity_created")
        if used_admin_fallback:
            steps_completed.append("opportunity_created_admin_fallback")
        logger.info(
            "STEP 1: New Opportunity created: %s (Account=%s)%s",
            opportunity_id, account_id,
            " [admin fallback]" if used_admin_fallback else "",
        )

    # ─── Shared post-creation steps ───
    _execute_post_opportunity_steps(
        sf=sf,
        sf_is_sandbox=sf_is_sandbox,
        opportunity_id=opportunity_id,
        account_id=account_id,
        contact_id=contact_id,
        advisor_salesforce_id=advisor_salesforce_id,
        advisor_name=advisor_name,
        sdr_salesforce_id=sdr_salesforce_id,
        sdr_name=sdr_name,
        sdr_email=sdr_email,
        client_name=client_name,
        patrimony_value=patrimony_value,
        profissao=profissao,
        interesse_investimentos=interesse_investimentos,
        description=description,
        event_datetime=event_datetime,
        duration_minutes=duration_minutes,
        modalidade=modalidade,
        is_consorcio=is_consorcio,
        # Os painéis do rodízio excluem só 'consorcio'; 'opportunity' marca a
        # linha do re-roteamento sem tirá-la da conta da fila (FBI-4719).
        opportunity_type=(
            "consorcio" if is_consorcio
            else "opportunity" if reused_opportunity
            else "account"
        ),
        flow_result=flow_result,
        steps_completed=steps_completed,
        errors=errors,
        # Consórcio fields — only needed for account flow (lead flow copies via conversion)
        idade=idade,
        modalidade_calculo=modalidade_calculo,
        id_carta=id_carta,
        tomador_decisao=tomador_decisao,
        intuito_consorcio=intuito_consorcio,
        interesses_consorcios=interesses_consorcios,
        reused_opportunity=reused_opportunity,
        source_opp_state=source_opp_state,
    )

    # ─── Final ───
    flow_result["success"] = (
        bool({"opportunity_created", "opportunity_reused"} & set(steps_completed))
        and R1_CRITICAL_STEPS.issubset(set(steps_completed))
    )
    logger.info(
        "R1 FROM OPP FLOW %s — steps: %s | errors: %s",
        "COMPLETED" if flow_result["success"] else "FAILED",
        steps_completed, errors,
    )
    return flow_result
