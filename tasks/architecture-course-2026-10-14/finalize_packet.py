import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[1]
packet_path = base / 'prepared-council/packet.json'
packet = json.loads(packet_path.read_text())
profile = json.loads((base / 'profile.json').read_text())
source_roots = {s['id']: Path(s['root']) for s in profile['sources']}
observed_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
approved_versions = {r['document_id']: r['document_sha256'] for r in packet['reviews']
                     if r['verdict'] == 'APPROVED'}
for document in packet['documents']:
    current = hashlib.sha256((root / document['path']).read_bytes()).hexdigest()
    if document['id'] in approved_versions:
        assert current == approved_versions[document['id']], document['id']
    document['sha256'] = current

new_evidence = {
    's2-reference-repair': ('workflow-evidence', 's2-reference-repair.md', 'contract'),
    's4-reference-repair': ('workflow-evidence', 's4-reference-repair.md', 'contract'),
    's6-reference-repair': ('workflow-evidence', 's6-reference-repair.md', 'contract'),
    'workflow-reference-repair': ('workflow-evidence', 'workflow-reference-repair.md', 'contract'),
    'guide-minio-lineage': ('workflow-evidence', 'guide-minio-lineage.json', 'contract'),
    'guide-minio-columns': ('workflow-evidence', 'guide-minio-columns.json', 'runtime'),
    'guide-minio-readback': ('workflow-evidence', 'guide-minio-readback.json', 'runtime'),
}
existing_ids = {e['id'] for e in packet['evidence']}
for evidence_id, (source_id, relative, kind) in new_evidence.items():
    if evidence_id in existing_ids:
        continue
    data = (source_roots[source_id] / relative).read_bytes()
    packet['evidence'].append({'id': evidence_id, 'source_id': source_id, 'path': relative,
                               'sha256': hashlib.sha256(data).hexdigest(),
                               'line_start': 1, 'line_end': len(data.decode().splitlines()),
                               'quote': data.decode(), 'observed_at': observed_at, 'kind': kind})

rendered = {}
for filename in ['mermaid-tutorials.json', 'mermaid-foundations.json',
                 'mermaid-foundations-repaired.json', 'mermaid-operations-platform.json',
                 'mermaid-sidecar-delta.json', 'mermaid-grok-repair.json']:
    receipt = json.loads((base / filename).read_text())
    for block in receipt['blocks']:
        if block['syntax']['status'] == 'PASS' and block['render']['status'] == 'PASS':
            rendered[(Path(block['path']).resolve(), block['source_sha256'])] = (filename, block)

semantic = {}
technical = json.loads((base / 'reviews/technical-semantic-recheck.json').read_text())
for item in technical['checks']:
    assert item['semantic_review'] == 'PASS'
    semantic[((root / item['document_path']).resolve(), item['source_sha256'])] = technical['reviewer_id']
teaching = json.loads((base / 'reviews/teaching-semantic-observations.json').read_text())
for item in teaching:
    assert item['semantic_verdict'] == 'APPROVED'
    doc = next(d for d in packet['documents'] if d['id'] == item['document_id'])
    semantic[((root / doc['path']).resolve(), item['source_sha256'])] = item['reviewer_id']
for filename in ['grok-response.json', 'grok-recheck-response.json']:
    response = json.loads((base / 'reviews' / filename).read_text())
    input_file = base / 'reviews/grok-initial-input.json'
    initial = json.loads(json.loads(input_file.read_text())['messages'][1]['content'])
    initial_diagrams = {d['document']['id']: d['diagrams'] for d in initial['documents']}
    for review in response['document_reviews']:
        doc = next(d for d in packet['documents'] if d['id'] == review['document_id'])
        current_fences = re.findall(r'(?m)^\s*(`{3,}|~{3,})mermaid[^\n]*\n([\s\S]*?)^\s*\1\s*$',
                                    (root / doc['path']).read_text())
        for item in review['diagram_reviews']:
            if item['status'] != 'PASS':
                continue
            if filename == 'grok-response.json':
                digest = initial_diagrams[doc['id']][item['fence_index'] - 1]['syntax']['source_sha256']
            else:
                digest = hashlib.sha256(current_fences[item['fence_index'] - 1][1].encode()).hexdigest()
            semantic[((root / doc['path']).resolve(), digest)] = response['reviewer_id']

packet['diagrams'] = []
bindings = []
for document in packet['documents']:
    path = root / document['path']
    fences = re.findall(r'(?m)^\s*(`{3,}|~{3,})mermaid[^\n]*\n([\s\S]*?)^\s*\1\s*$', path.read_text())
    for index, (_, body) in enumerate(fences, 1):
        digest = hashlib.sha256(body.encode()).hexdigest()
        key = (path.resolve(), digest)
        assert key in rendered, (document['id'], index, 'missing render')
        assert key in semantic, (document['id'], index, 'missing independent semantics')
        filename, block = rendered[key]
        diagram = {'id': f"{document['id']}#mermaid-{index}", 'document_id': document['id'],
                   'fence_index': index, 'relation_ids': document['relation_ids'],
                   'syntax': block['syntax'], 'render': block['render'], 'semantic_review': 'PASS'}
        packet['diagrams'].append(diagram)
        bindings.append({'diagram_id': diagram['id'], 'source_sha256': digest,
                         'render_receipt': filename, 'semantic_reviewer': semantic[key]})
packet['status'] = 'DRAFT'
packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n')
(base / 'artifacts/final-diagram-bindings.json').write_text(json.dumps(bindings, indent=2) + '\n')
print(json.dumps({'documents': len(packet['documents']), 'diagrams': len(packet['diagrams']),
                  'independent_approvals_preserved': len(packet['reviews']),
                  'evidence': len(packet['evidence'])}))
