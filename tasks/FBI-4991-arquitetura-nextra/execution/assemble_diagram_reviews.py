"""Bind actual independent diagram judgments to the current diagram bytes."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
REVIEW = BASE / 'reviews'


def read(name):
    return json.loads((REVIEW / name).read_text())


records = {}
one = read('diagram-semantics-one.json')
one_fix = read('diagram-semantics-one-recheck.json')
two = read('diagram-semantics-two.json')
two_fix = read('diagram-semantics-two.recheck.json')
terminal = read('terminal-diagrams.json')

for item in one['items']:
    current = dict(item)
    receipt = 'diagram-semantics-one.json'
    if item['id'] == one_fix['item']['id']:
        fixed = one_fix['item']
        current.update(fixed, documentSHA=fixed['current_documentSHA'], bodySHA=fixed['current_bodySHA'])
        receipt = 'diagram-semantics-one-recheck.json'
    for rebind in one_fix['deterministic_doc_rebinds']:
        if item['id'] == rebind['id']:
            assert current['bodySHA'] == rebind['bodySHA'] and rebind['body_unchanged']
            current['documentSHA'] = rebind['current_documentSHA']
            current['document_hash_rebind_receipt'] = 'diagram-semantics-one-recheck.json'
    document = Path(current['document'])
    document = str(document.relative_to(ROOT)) if document.is_absolute() else str(document)
    records[item['id']] = dict(id=item['id'], document=document, document_sha256=current['documentSHA'],
        body_sha256=current['bodySHA'], status=current['status'], reviewer=one['reviewer'],
        receipt=receipt, judgment=current)

carry = {item['id']: item for item in two_fix['carried_forward_diagrams']}
for item in two['diagrams']:
    fixed = carry[item['id']]
    assert fixed['status'] == 'PASS_BOUNDED'
    assert item['id'] not in records
    records[item['id']] = dict(id=item['id'], document=fixed['document'],
        document_sha256=fixed['document_sha256'], body_sha256=fixed['body_sha256'],
        status=fixed['status'], reviewer=two['reviewer'], receipt='diagram-semantics-two.recheck.json',
        initial_receipt='diagram-semantics-two.json', judgment=item,
        repair_judgment=two_fix['finding_resolution'] if item['id'] == 'diagram-39' else None)

for item in terminal['diagrams']:
    assert item['diagram_id'] not in records
    records[item['diagram_id']] = dict(id=item['diagram_id'], document=item['document_path'],
        document_sha256=item['document_sha256'], body_sha256=item['diagram_source_sha256'],
        status=item['semantic_verdict'], reviewer=terminal['reviewer'],
        receipt='terminal-diagrams.json', judgment=item)

rendered = json.loads((BASE / 'mermaid-current.json').read_text())
assert len(records) == len(rendered['blocks']) == 94
for index, block in enumerate(rendered['blocks'], 1):
    record = records[f'diagram-{index}']
    assert record['status'] == 'PASS_BOUNDED', record['id']
    assert (ROOT / record['document']).resolve() == Path(block['path']).resolve()
    assert record['document_sha256'] == block['document_sha256'] == hashlib.sha256((ROOT / record['document']).read_bytes()).hexdigest()
    assert record['body_sha256'] == block['source_sha256'], record['id']
    record['fence_index'] = block['fence_index']

source_names = ['diagram-semantics-one.json', 'diagram-semantics-one-recheck.json',
    'diagram-semantics-two.json', 'diagram-semantics-two.recheck.json', 'terminal-diagrams.json']
output = dict(observed_at=datetime.now(timezone.utc).isoformat(), verdict='PASS_BOUNDED',
    semantic_reviewed=94, unresolved_high=0, count_is_not_approval=True,
    scope='Independent judgments certify the stated historical source, proposal or lab abstraction; they do not certify current production execution.',
    source_receipts=[dict(path=str((REVIEW / name).relative_to(ROOT)), sha256=hashlib.sha256((REVIEW / name).read_bytes()).hexdigest()) for name in source_names],
    backlog=[*one['backlog'], *two['backlog']],
    diagrams=sorted(records.values(), key=lambda record: int(record['id'].split('-')[1])))
(REVIEW / 'diagram-semantic-closure.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: output[key] for key in ['verdict', 'semantic_reviewed', 'unresolved_high']}))
