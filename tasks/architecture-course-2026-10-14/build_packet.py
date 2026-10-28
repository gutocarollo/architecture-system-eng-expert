import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


base = Path(__file__).resolve().parent
profile = json.loads((base / 'profile.json').read_text())
project_root = Path(profile['project_root']).resolve()
source_roots = {item['id']: Path(item['root']).resolve() for item in profile['sources']}
observed_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
coverage = json.loads((base / 'evidence/coverage.json').read_text())
packet = json.loads((base / 'prepared-council/packet.json').read_text())
if packet.get('reviews'):
    raise RuntimeError('The reviewed packet is frozen. Apply bounded document/evidence updates without resetting reviews or timestamps.')
packet.update(created_at=observed_at, status='DRAFT', scope=profile['context']['bounded_anchor'])
packet['inventory'] = [item['concept_id'] for item in coverage['concepts']]
packet['evidence'] = []
packet['sources'] = []
packet['relations'] = []
packet['documents'] = []
packet['diagrams'] = []
packet['reviews'] = []
packet['adrs'] = []
packet['gaps'] = []


def add_evidence(evidence_id, source_id, relative_path, line_start, line_end, kind):
    path = source_roots[source_id] / relative_path
    data = path.read_bytes()
    lines = data.decode().splitlines(keepends=True)
    quote = ''.join(lines[line_start - 1:line_end])
    if not quote:
        raise ValueError(f'Empty evidence: {evidence_id}')
    packet['evidence'].append({
        'id': evidence_id, 'source_id': source_id, 'path': relative_path,
        'sha256': hashlib.sha256(data).hexdigest(), 'line_start': line_start,
        'line_end': min(line_end, len(lines)), 'quote': quote,
        'observed_at': observed_at, 'kind': kind,
    })
    return evidence_id


def relation(relation_id, producer, consumer, producer_id, consumer_id, bridge_id, contract):
    packet['relations'].append({
        'id': relation_id, 'relation_kind': 'runtime', 'producer': producer,
        'consumer': consumer, 'mechanism': 'Declared Python method call',
        'contract': contract, 'correlation': 'Static caller, method name and request arguments',
        'failure_recovery': 'The referenced code describes the local path; no recent execution or global recovery guarantee is claimed.',
        'environment': 'MakersHub local checkout',
        'deployment_scope': 'File hashes in the evidence; runtime deployment is not inferred.',
        'status': 'DECLARED', 'critical': True,
        'producer_evidence': [producer_id], 'consumer_evidence': [consumer_id],
        'bridge_evidence': [bridge_id],
    })


for source_id, root in source_roots.items():
    revision = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    packet['sources'].append({'id': source_id, 'revision': revision or 'dated-local-captures',
                              'observed_at': observed_at, 'state': 'AVAILABLE',
                              'reason': 'Local source or dated capture available; reported runtime timestamps remain scoped to their original observations.'})

reports = {
    's1': 's1-design.md', 's2': 's2-application.md', 's3': 's3-airflow.md',
    's4': 's4-consistency.md', 's5': 's5-operations.md', 's6': 's6-platform.md',
    'bootstrap': 'bootstrap.md',
}
for evidence_id, name in reports.items():
    path = source_roots['workflow-evidence'] / name
    add_evidence(evidence_id, 'workflow-evidence', name, 1, len(path.read_text().splitlines()), 'contract')

for prefix in ('l1a-', 'l1b-', 'l1c-', 'l2a-', 'l2b-', 'l2c-', 'l3a-', 'l3b-', 'l3c-', 'l4a-', 'l4b-', 'l4c-', 'l5a-', 'l5b-', 'l5c-', 'l6a-', 'l6b-', 'l6c-'):
    matches = sorted(source_roots['workflow-evidence'].glob(prefix + '*.md'))
    if matches:
        selected = matches[0]
        add_evidence(prefix.rstrip('-'), 'workflow-evidence', selected.name, 1, len(selected.read_text().splitlines()), 'contract')
add_evidence('original-request', 'project', 'tasks/architecture-course-2026-10-14/original-request.md', 1, 200, 'contract')
add_evidence('original-catalog', 'project', 'docs/catalogos/catalogo-patterns.md', 1, 400, 'contract')

add_evidence('inflow-query', 'workflow-evidence', 'postgres-inflow.json', 1, 60, 'runtime')
add_evidence('report-api', 'makershub', 'backend/app/api/v1/report_data.py', 50, 77, 'code')
add_evidence('report-service', 'makershub', 'backend/app/services/report_read_service.py', 16, 54, 'code')
add_evidence('report-repository', 'makershub', 'backend/app/repositories/report_read_repository.py', 191, 281, 'code')
add_evidence('insurance-api', 'makershub', 'backend/app/api/v1/insurance.py', 46, 72, 'code')
add_evidence('insurance-service', 'makershub', 'backend/app/services/insurance_service.py', 5, 24, 'code')
add_evidence('insurance-repository', 'makershub', 'backend/app/repositories/insurance_repo.py', 74, 101, 'code')
add_evidence('idempotency-code', 'makershub', 'backend/app/services/idempotency_store.py', 70, 120, 'code')
add_evidence('pending-intent-code', 'makershub', 'backend/app/services/absence_reassignment_service.py', 337, 418, 'code')
add_evidence('competing-claims-code', 'makershub', 'backend/app/repositories/lead_pipeline_repository.py', 485, 515, 'code')

relation('report-api-service', 'report_data API', 'ReportReadService.read', 'report-api', 'report-service', 'report-api', 'ReportReadParams with filters and pagination')
relation('report-service-repository', 'ReportReadService.read', 'ReportReadRepository.read', 'report-service', 'report-repository', 'report-service', 'ReportReadPort request and rows')
relation('insurance-api-service', 'insurance KPI API', 'InsuranceService.get_kpi_metrics', 'insurance-api', 'insurance-service', 'insurance-api', 'Date filters and KPI result; cache TTL declared in route')
relation('insurance-service-repository', 'InsuranceService.get_kpi_metrics', 'InsuranceRepository.get_kpi_metrics', 'insurance-service', 'insurance-repository', 'insurance-service', 'Date filters passed to repository')

packet['coverage'] = {
    'L0': {'status': 'COVERED', 'evidence_ids': ['report-api', 'report-service', 'report-repository'], 'reason': 'Representative symbols have exact local file and line evidence.'},
    'L1': {'status': 'COVERED', 'evidence_ids': ['s2', 's4', 's5'], 'reason': 'The six specialist packets delimit the modules used as examples.'},
    'L2': {'status': 'COVERED', 'evidence_ids': ['s3', 's6'], 'reason': 'Process configuration is recorded with environment and original UTC observation time.'},
    'L3': {'status': 'COVERED', 'evidence_ids': ['s2', 's3', 's6'], 'reason': 'Local checkout, server source and Kubernetes source are explicitly distinguished.'},
    'L4': {'status': 'COVERED', 'evidence_ids': ['s3', 'bootstrap', 'inflow-query'], 'reason': 'External integration contracts, graph and database captures are scoped; execution of every external effect is not claimed.'},
}

for path in sorted((project_root / 'content').rglob('*.mdx')):
    relative = path.relative_to(project_root).as_posix()
    document_id = relative.removeprefix('content/').removesuffix('.mdx')
    text = path.read_text()
    author_id = '/root'
    for chapter in coverage['chapters']:
        if relative == chapter['path']:
            owner = chapter['proposed_owner']
            author_id = profile['council']['planners'][int(owner[1:]) - 1]
    if relative.startswith('content/tutoriais/') or relative == 'content/guias/investigar-impacto.mdx':
        author_id = '/root/s1_learning_design'
    group_match = re.match(r'content/referencia/catalogo/(\d{2})-', relative)
    if group_match:
        group_owners = {1: 2, 2: 4, 3: 4, 4: 4, 5: 4, 6: 5, 7: 5, 8: 5,
                        9: 5, 10: 2, 11: 6, 12: 6, 13: 6, 14: 6, 15: 5, 16: 3, 17: 2}
        owner_number = group_owners.get(int(group_match[1]))
        if owner_number:
            author_id = profile['council']['planners'][owner_number - 1]
    inventory_ids = [item['concept_id'] for item in coverage['concepts']
                     if item.get('explanation_path') == relative or relative in item.get('reference_paths', [])]
    if relative.endswith('/prioritarios.mdx'):
        inventory_ids = [item['concept_id'] for item in coverage['concepts'] if item['priority_entries']]
    relation_ids = []
    if any(term in text for term in ['ReportReadService', 'ReportReadRepository']):
        relation_ids.extend(['report-api-service', 'report-service-repository'])
    if 'InsuranceService' in text or 'InsuranceRepository' in text:
        relation_ids.extend(['insurance-api-service', 'insurance-service-repository'])
    packet['documents'].append({'id': document_id, 'path': relative,
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                'author_id': author_id, 'inventory_ids': inventory_ids,
                                'relation_ids': relation_ids})
    fences = re.findall(r'(?m)^\s*(`{3,}|~{3,})mermaid[^\n]*\n([\s\S]*?)^\s*\1\s*$', text)
    for index, (_, source) in enumerate(fences, 1):
        digest = hashlib.sha256(source.encode()).hexdigest()
        packet['diagrams'].append({'id': f'{document_id}#mermaid-{index}', 'document_id': document_id,
                                  'fence_index': index, 'relation_ids': relation_ids,
                                  'syntax': {'status': 'NOT_RUN', 'tool': '', 'version': '', 'source_sha256': digest},
                                  'render': {'status': 'NOT_RUN', 'tool': '', 'version': '', 'source_sha256': digest},
                                  'semantic_review': 'NOT_RUN'})

packet['gaps'] = [
    {'id': 'runtime-execution-scope', 'kind': 'scope', 'critical': False, 'source_id': 'workflow-evidence',
     'description': 'Selected code and configuration are verified; no claim that every DAG, endpoint or consumer executed recently.'},
    {'id': 'graph-snapshot-age', 'kind': 'freshness', 'critical': False, 'source_id': 'workflow-evidence',
     'description': 'Graph built 2026-10-13; its runtime statistics were stale. Only explicitly dated lineage counts are used.'},
]
(base / 'prepared-council/packet.json').write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': packet['status'], 'evidence': len(packet['evidence']),
                  'relations': len(packet['relations']), 'documents': len(packet['documents']),
                  'diagrams': len(packet['diagrams'])}))
