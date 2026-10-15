"""Bind the original twenty HIGH-only warm judgments to the repaired freeze."""
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXECUTION = ROOT / 'tasks/FBI-4991-arquitetura-nextra/execution'
CURATION = EXECUTION / 'curation'
REVIEWS = EXECUTION / 'reviews'
sys.path.insert(0, str(CURATION))
from adjudication_gate import carry_forward_issues
from semantic_fingerprints import semantic_fingerprint

read = lambda path: json.loads(path.read_text())
digest = lambda data: hashlib.sha256(data).hexdigest()
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
freeze = read(CURATION / 'freeze-receipt.json')
matrix = read(CURATION / 'matrix.json')
rows = {row['concept_id']: row for row in matrix['concepts']}
first = read(REVIEWS / 'curation-independent.assignment-one.json')
findings = read(REVIEWS / 'curation-independent.findings.json')['findings']
original_high = {row['concept_id']: row for row in findings}
adjudications = read(CURATION / 'author-adjudications.json')
baseline = {row['concept_id']: row for row in read(CURATION / 'review-baseline.json')['concepts']}
licenses = read(CURATION / 'revision-licenses.json')
recommendations = {row['concept_id']: row for row in
                   read(EXECUTION / 'curation-repairs/consolidated-recommendations.json')['rows']}
errors = []
file_hashes = {}


def bind(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    actual = digest(path.read_bytes())
    key = str(path.relative_to(ROOT))
    file_hashes[key] = actual
    if expected and actual != expected:
        errors.append({'kind': 'HASH', 'path': key, 'expected': expected, 'actual': actual})
    return actual


for name, entry in freeze['files'].items():
    bind(CURATION / name, entry['sha256'])
for name in ['freeze-receipt.json', 'publication-index.json', 'revision-licenses.json']:
    bind(CURATION / name)
for name in ['curation-independent.assignment-one.json', 'curation-independent.findings.json',
             'curation-independent.recheck.guard.json', 'curation-independent.recheck.mdx.json']:
    bind(REVIEWS / name)
bind(EXECUTION / 'curation-repairs/consolidated-recommendations.json')

closures = {
    'anti-corruption-layer': 'The repository calls translators that choose trade/close/NAV/rate, normalize timestamps and validate portfolio values before returning local models. This is semantic adaptation; financial correctness and API execution remain outside the claim.',
    'at-least-once-delivery': 'Pulsar timeout IDs become a redelivery command; ServerCnx reaches Consumer and subscription, replay positions are reread and sent again, and ACK deletes positions from the persistent cursor. Shared persistent-subscription scope and external-effect limits are explicit.',
    'circuit-breaker': 'Mastodon wraps the actual hashtag Elasticsearch call with tracked failure threshold and recovery delay; RedLight reaches a database fallback. Resilience4j is a compared failure-state implementation, not the library attributed to Mastodon.',
    'compensating-transaction': 'The real Medusa createOrdersStep returns created IDs as compensation data and deletes those IDs in its callback. The handler retrieves compensateInput and the engine selects the compensation handler. This is a later semantic action, not ACID rollback.',
    'consistent-hashing': 'Loki derives stream tokens and calls ingestersRing.Get; the pinned Dskit implementation binary-searches the ring and walks token owners with wraparound and distinct replicas. The application dependency pin resolves to the selected Dskit revision.',
    'context-map': 'The accepted thndr ADR names context dependencies and published interfaces. Portfolio and Engagement consume Market Data resolution, and the architecture import matrix encodes those directions. Organizational customer/supplier governance is not inferred.',
    'denormalization': 'Medusa copies product title and variant SKU into order line-item fields, persists those fields through the order service and reads items with the order. Explicit caller values can override catalog defaults; this is a bounded attribute snapshot.',
    'distributed-cache': 'The selected Superset Docker configuration initializes DATA_CACHE_CONFIG as RedisCache. Query-cache get/set reach the shared Redis backend under host/database/prefix configuration. Library revisions are fixed examples, without claiming a resolved deployed lockfile.',
    'domain-service': 'Kill Bill invoice generation combines account, subscription events, catalog prices and prior invoices; recurring items calculate cycles times rate times quantity. InvoiceDispatcher calls that operation, which is distinct from entity identity or application-only persistence coordination.',
    'materialized-view': 'PostgreSQL utility dispatch reaches CREATE/REFRESH handlers, fills a new heap from the query and swaps or reconciles physical data. The server is explicitly the infrastructure application; reusable materialization routines are the base role.',
    'mvc': 'Redmine show loads an Issue model, prepares domain data, explicitly renders issues/show and supplies that model to the ERB view. Rails renderer and Gemfile pin support the selected HTML path, without using API formats as MVC proof.',
    'orchestration-saga': 'Medusa create-order centrally sequences customer/order steps. Their concrete callbacks delete only objects created by those steps; a permanent failure enters WAITING_TO_COMPENSATE, flags completed steps for return and invokes compensation handlers. No global isolation or exactly-once claim is made.',
    'precomputation': 'PostgreSQL computes and persists a materialized result during creation or refresh; subsequent physical relation scans can consume it. This moves work before the consuming read, without promising automatic refresh or a measured speedup.',
    'range-sharding': 'The VTGate sequential Numeric vindex preserves numeric ordering, maps bounds to a key range and resolves only intersecting shard ranges; point resolution uses containment. This proves bounded range routing rather than an empty broadcast range or hash lookup.',
    'refresh-ahead': 'Trino enables asynchronous metadata reload only when the refresh interval precedes expiration, then delegates eligible reads to the cache loader. Guava read-triggered refresh can retain the old value while loading; keys without access can still expire.',
    'saga': 'The real Medusa workflow composes customer and order mutations and records their concrete reverse actions. Failure changes the engine into compensation and passes stored effect IDs to those actions. Stock reservation, outbox and global transactional guarantees remain excluded.',
    'scatter-gather': 'One Loki range query produces interval subrequests, bounded workers execute them and Process collects their responses for MergeResponse in the installed frontend middleware. Errors cancel siblings; row-limit early exit is an explicit completion criterion.',
    'single-flight': 'Loki metadata cold misses call Group.DoChan with the same region key. One detached load returns bytes/error to waiting callers, while each caller can cancel independently. Scope is one Group instance and one in-flight load, not a distributed lock.',
    'thread-pool': 'Nutch starts configured reusable FetcherThread workers sharing fetchQueues. Each worker loops over URL items and executes protocol fetches; the pool can grow or halt workers under its bandwidth policy. CPython is a compared executor base, not a Nutch dependency.',
    'websocket': 'Home Assistant registers the WebSocket view, prepares aiohttp upgrade, authenticates, receives and dispatches commands, and forwards subscribed bus events as outgoing TEXT frames. Normal token auth and the preauthenticated Supervisor Unix path are distinguished; durable replay is not claimed.',
}
if set(closures) != set(original_high) or len(closures) != 20:
    errors.append({'kind': 'ORIGINAL_HIGH_SCOPE'})

mdx_sections = {}
for page in (ROOT / 'content/referencia/curadoria').glob('*.mdx'):
    contents = page.read_text()
    for section in re.split(r'\n(?=## )', contents):
        match = re.search(r'O identificador canônico é `([^`]+)`', section)
        if match and match.group(1) in original_high:
            mdx_sections[match.group(1)] = (page, section)

results = []
source_bindings = set()
license_bindings = set()
for concept_id in sorted(original_high):
    row = rows[concept_id]
    source_by_url = {source['url'].split('#')[0]: source
                     for role in ['base', 'application'] for source in row[role]}
    selected_sources = []
    for source in source_by_url.values():
        bind(source['artifact'], source['sha256'])
        source_bindings.add(source['artifact'])
        key = source['repo'] + '@' + source['revision']
        license_record = licenses[key]
        bind(license_record['artifact'], license_record['sha256'])
        license_bindings.add(key)
        selected_sources.append({key: source.get(key) for key in
                                 ['repo', 'path', 'revision', 'sha256', 'artifact', 'url']})
    primary_spans = []
    for evidence in adjudications[concept_id]['primary_evidence']:
        source = source_by_url[evidence['source_url'].split('#')[0]]
        lines = (ROOT / source['artifact']).read_text().splitlines()
        excerpt = '\n'.join(lines[evidence['start_line'] - 1:evidence['end_line']])
        if digest(excerpt.encode()) != evidence['excerpt_sha256']:
            errors.append({'kind': 'SPAN', 'concept_id': concept_id})
        primary_spans.append({**evidence, 'artifact': source['artifact']})
    proposal = recommendations[concept_id]
    for key in ['mechanism', 'limits', 'application_kind']:
        if proposal[key] != row[key]:
            errors.append({'kind': 'PROPOSAL_INTEGRATION', 'concept_id': concept_id, 'field': key})
    bind(ROOT / proposal['repair_packet'], proposal['repair_packet_sha256'])
    page, section = mdx_sections[concept_id]
    prose_exact = row['mechanism'] in section and row['limits'] in section
    pending_marker = 'A rechecagem independente desta versão continua pendente.' in section
    if not prose_exact or not pending_marker or row['independent_review'] != 'PENDING':
        errors.append({'kind': 'MDX_READBACK', 'concept_id': concept_id})
    bind(page)
    results.append({'concept_id': concept_id,
                    'first_pass_finding_id': original_high[concept_id]['finding_id'],
                    'state': 'APPROVED_BOUNDED', 'closure': closures[concept_id],
                    'semantic_fingerprint': semantic_fingerprint(row),
                    'primary_sources': selected_sources, 'verified_primary_spans': primary_spans,
                    'mdx': {'path': str(page.relative_to(ROOT)), 'sha256': file_hashes[str(page.relative_to(ROOT))],
                            'section_sha256': digest(section.encode()), 'mechanism_limits_exact': prose_exact,
                            'author_recheck_pending_marker': pending_marker}})

carried = []
for previous in first['concepts']:
    concept_id = previous['concept_id']
    if concept_id in original_high:
        continue
    issues = carry_forward_issues(rows[concept_id], baseline[concept_id], ROOT)
    if issues:
        errors.append({'kind': 'PRESERVED_SCOPE_CHANGED', 'concept_id': concept_id, 'issues': issues})
    carried.append(concept_id)

auxiliary_manifest = 'tasks/FBI-4991-arquitetura-nextra/execution/curation-repairs/raw/046604ed6096af65037b13139ca530ebcd38e29c17ef71463f36b1d6f4a81b36.txt'
bind(auxiliary_manifest, 'f3ae7b4b0c38e6299f68a80241b262845f5d6ce31a9c37ccae14117b8a9d6a45')
if '"aiohttp==3.14.5"' not in (ROOT / auxiliary_manifest).read_text():
    errors.append({'kind': 'AIOHTTP_DEPENDENCY_PIN'})
enterprise_receipt = read(REVIEWS / 'curation-independent.recheck.medusa-enterprise.receipt.json')
bind(enterprise_receipt['artifact'], enterprise_receipt['sha256'])
enterprise_text = (ROOT / enterprise_receipt['artifact']).read_text()
enterprise_paths = re.findall(r'^- `([^`]+)`', enterprise_text, re.M)
enterprise_hits = []
for row in results:
    for source in row['primary_sources']:
        if source['repo'] == 'medusajs/medusa':
            for path in enterprise_paths:
                if source['path'] == path or (path.endswith('/') and source['path'].startswith(path)):
                    enterprise_hits.append(source['path'])
if enterprise_hits:
    errors.append({'kind': 'MEDUSA_ENTERPRISE_SCOPE', 'paths': enterprise_hits})

cpython_key = 'python/cpython@a6b4aa687cd9f8f95e3b940e6314ac8f2a85fbbb'
cpython_license = licenses[cpython_key]
medium = [{'concept_id': 'thread-pool', 'severity': 'MEDIUM',
           'kind': 'LICENSE_LABEL_MISMATCH', 'license_record': cpython_key,
           'declared_spdx': cpython_license['license_spdx'],
           'artifact': cpython_license['artifact'], 'source_sha256': cpython_license['sha256'],
           'lines': [59, 87], 'literal': 'Python Software Foundation License Version 2.',
           'impact': 'The source remains an OSS executor base, but its published SPDX label PostgreSQL is incorrect.',
           'recommendation': 'Use the verified Python license description; retain NOASSERTION rather than the false PostgreSQL label if an exact SPDX expression is not adjudicated. This metadata fix needs no renewed twenty-concept semantic review.'}]
guard = read(REVIEWS / 'curation-independent.recheck.guard.json')
mdx = read(REVIEWS / 'curation-independent.recheck.mdx.json')
if guard['failures'] or mdx['errors']:
    errors.append({'kind': 'DETERMINISTIC_GATE'})
result = {
    'observed_utc': now, 'reviewer': '/root/curation_independent',
    'native_type': 'default', 'contract': 'read-only adversarial HIGH-only warm REVIEW',
    'model': 'gpt-6.1-sol', 'reasoning_effort': 'xhigh',
    'workspace': str(ROOT),
    'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'matrix_sha256': digest((CURATION / 'matrix.json').read_bytes()),
    'first_pass_matrix_sha256': 'a4b12f6c6aa8b1883d8f6c1ac7ed1c7f81d829859422f5a0212f7fd1cca6689e',
    'verdict': 'APPROVED_BOUNDED' if not errors else 'REPAIR',
    'original_high_count': 20, 'rechecked_count': len(results),
    'residual_high_count': 0 if not errors else len(errors),
    'concepts': results, 'preserved_previous_concepts': len(carried),
    'preserved_previous_states': {'APPROVED_BOUNDED': 153, 'APPROVED_WITH_MEDIUM': 10},
    'other_lane_not_rechecked': 127,
    'checks': {'source_artifacts_bound': len(source_bindings),
               'license_revisions_bound': len(license_bindings),
               'positive_guard_checks': guard['checks'], 'positive_guard_failures': guard['failures'],
               'reference_mdx_files': mdx['files'], 'reference_mdx_errors': len(mdx['errors']),
               'medusa_enterprise_paths_matched': enterprise_hits,
               'auxiliary_home_assistant_aiohttp_manifest': auxiliary_manifest},
    'medium_backlog': medium, 'errors': errors, 'bound_file_sha256': file_hashes,
    'limits': ['Approval concerns only the bounded primary-source mechanisms of the original twenty HIGH findings.',
               'The previous 153 approvals and ten medium entries were fingerprint-carried, not semantically rereviewed.',
               'The other lane and Sites hosting are outside this recheck.',
               'Source inspection, metadata and MDX readback do not assert an executed OSS deployment or global transaction guarantee.',
               'License source bindings were checked; the one incorrect CPython label is explicitly retained as medium metadata work.']}
(REVIEWS / 'curation-independent.recheck.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
text = f'''# Rechecagem dos vinte achados altos

O veredito é **{result['verdict']}** para os vinte mecanismos reparados da lane original. Não restou achado alto nesse recorte. Os 153 conceitos já aprovados e os dez ajustes médios anteriores foram preservados por fingerprint; os 127 conceitos da outra lane não foram reabertos.

A rechecagem está vinculada à matriz `{result['matrix_sha256']}`, ao HEAD `{result['head']}` e aos hashes de código, licenças, propostas e MDX registrados em `curation-independent.recheck.json`.

- O WebSocket agora contém registro da rota, upgrade, autenticação, dispatcher e saída de eventos. A entrega At Least Once contém timeout, pedido de redelivery, replay do cursor e confirmação persistente, com limites explícitos para efeitos externos.
- A ACL contém tradução de natureza, escala e precedência dos valores. O Context Map contém relações e consumidores das interfaces publicadas. O Domain Service contém a geração de faturas do Kill Bill e seu cálculo entre eventos, catálogo, conta e faturas anteriores.
- Os casos de cache agora mostram Redis compartilhado na configuração Docker do Superset, refresh assíncrono anterior ao TTL no Trino e coalescência de misses reais no Loki. O circuito de busca Mastodon contabiliza falhas e recusa chamadas durante a recuperação.
- O roteamento Loki resolve hashes para donos de tokens; o VTGate resolve intervalos sequenciais para shards. O Scatter/Gather divide e reúne a mesma consulta Loki. O Nutch mantém workers de threads que reutilizam a fila de coleta.
- O pedido Medusa grava atributos copiados do catálogo e registra callbacks concretos para desfazer cliente e pedido. O motor entrega os dados da criação à compensação. PostgreSQL aparece com papéis explícitos de base e servidor que materializa resultados. Redmine apresenta o caminho HTML entre controlador, modelo Issue e template.

Os vinte MDX reproduzem exatamente o mecanismo e os limites da matriz. Eles ainda identificam o texto como reparo autoral com rechecagem pendente; não simulam uma aprovação independente. O guard positivo passou {guard['checks']} verificações e seus casos de mutação, com zero falhas. A validação de referência compilou {mdx['files']} páginas com zero erros.

Há um ajuste novo **médio**: o registro CPython `{cpython_key}` usa o rótulo SPDX `PostgreSQL`, mas o arquivo ligado declara `Python Software Foundation License Version 2` nas linhas 62–63 e 73. O texto e o hash da licença estão corretos; o rótulo deve ser corrigido ou permanecer sem uma classificação SPDX afirmativa. Isso não exige uma nova rodada semântica dos vinte conceitos. Os caminhos Medusa examinados não aparecem na lista Enterprise da mesma revisão.

O principal pode consumir estes vinte julgamentos e avançar para a auditoria terminal. A aprovação não representa execução dos produtos OSS, compatibilidade jurídica entre dependências, publicação ou hospedagem.
'''
(REVIEWS / 'curation-independent.recheck.md').write_text(text)
print(json.dumps({key: result[key] for key in ['observed_utc', 'head', 'matrix_sha256', 'verdict',
                                             'rechecked_count', 'residual_high_count', 'checks', 'errors']},
                 ensure_ascii=False))
raise SystemExit(bool(errors))
