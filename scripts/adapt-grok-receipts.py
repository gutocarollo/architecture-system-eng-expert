import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'tasks/architecture-course-2026-10-14'
sys.path.insert(0, '/Users/augustocarollo/skills/docs-autoagents/scripts')
from docs_workflow import review_context_digest

packet_path = BASE / 'prepared-council/packet.json'
packet = json.loads(packet_path.read_text())
recheck = '--recheck' in sys.argv[1:]
prefix = 'grok-recheck' if recheck else 'grok'
response = json.loads((BASE / f'reviews/{prefix}-response.json').read_text())
dispatch = json.loads((BASE / f'reviews/{prefix}-dispatch.json').read_text())
assert dispatch['http_status'] == 200
assert dispatch['model_returned'] == 'x-ai/grok-4.7'
assert response['reviewer_id'] == 'openrouter/x-ai/grok-4.7'
documents = {d['id']: d for d in packet['documents']}
pending = {'explicacoes/cache/index', 'explicacoes/capacity/index',
           'referencia/catalogo/06-cache'}
if recheck:
    pending = set()
bindings = []
for review in response['document_reviews']:
    if review['document_id'] in pending:
        continue
    assert review['verdict'] == 'APPROVED' and not review['open_high_findings']
    assert all(d['status'] == 'PASS' for d in review['diagram_reviews'])
    document = documents[review['document_id']]
    assert set(document['relation_ids']).issubset(set(review['relation_ids']))
    assert document['sha256'] == review['document_sha256']
    assert hashlib.sha256((ROOT / document['path']).read_bytes()).hexdigest() == document['sha256']
    digest, projection = review_context_digest(packet, document['id'], review['evidence_ids'])
    receipt = {k: review[k] for k in ('document_id', 'document_sha256', 'verdict',
                                     'open_high_findings', 'relation_ids', 'evidence_ids')}
    receipt.update(receipt_version=1, reviewer_id=response['reviewer_id'],
                   dispatch_id=dispatch['dispatch_id'], context_sha256=digest)
    receipt['relation_ids'] = document['relation_ids']
    receipt_path = BASE / ('reviews/grok-' + document['id'].replace('/', '-') + '.json')
    assert not receipt_path.exists()
    data = (json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode()
    receipt_path.write_bytes(data)
    packet['reviews'].append({
        **{k: receipt[k] for k in ('reviewer_id', 'document_id', 'document_sha256',
                                  'verdict', 'open_high_findings')},
        'receipt_path': receipt_path.relative_to(ROOT).as_posix(),
        'receipt_sha256': hashlib.sha256(data).hexdigest()})
    for reviewed_diagram in review['diagram_reviews']:
        diagram = next(d for d in packet['diagrams']
                       if d['document_id'] == document['id']
                       and d['fence_index'] == reviewed_diagram['fence_index'])
        diagram['semantic_review'] = 'PASS'
    bindings.append({'document_id': document['id'],
                     'submitted_context_sha256': review['context_sha256'],
                     'projected_selected_evidence_sha256': digest,
                     'original_adjudicated_relation_ids': review['relation_ids'],
                     'document_relation_ids': document['relation_ids'],
                     'evidence_ids': review['evidence_ids']})
packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n')
(BASE / f'reviews/{prefix}-receipt-adapter.json').write_text(json.dumps({
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'dispatch_id': dispatch['dispatch_id'], 'response_sha256': dispatch['output_sha256'],
    'binding_owner': 'Root mechanical receipt adapter',
    'scope': 'The unchanged model verdict is bound to the exact current document and the evidence IDs actually named by the reviewer. The submitted digest covered the full supplied context; this adapter calculates the canonical projection for the selected IDs. No vote or finding was changed.',
    'bindings': bindings}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'actual_approvals_adapted': len(bindings), 'pending': sorted(pending)}))
