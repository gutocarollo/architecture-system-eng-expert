#!/usr/bin/env python3
"""Preserve completed first-pass decisions; never edit the frozen matrix."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
from semantic_fingerprints import semantic_fingerprint

BASE = Path(__file__).resolve().parent
FROZEN = BASE.parent / 'curation'
REVIEW = BASE.parent / 'reviews'
matrix_bytes = (FROZEN / 'matrix.json').read_bytes()
matrix_hash = hashlib.sha256(matrix_bytes).hexdigest()
assert matrix_hash == 'a4b12f6c6aa8b1883d8f6c1ac7ed1c7f81d829859422f5a0212f7fd1cca6689e'
matrix = json.loads(matrix_bytes)
judgments = {}
reports = []
for name in ['curation-independent.concepts.json', 'curation-second.concepts.json']:
    contents = (REVIEW / name).read_bytes()
    report = json.loads(contents)
    reports.append({'path': str((REVIEW / name).relative_to(BASE.parents[3])),
                    'sha256': hashlib.sha256(contents).hexdigest()})
    for entry in report['concepts']:
        if entry['state'] == 'UNREVIEWED':
            continue
        assert entry['concept_id'] not in judgments, entry['concept_id']
        judgments[entry['concept_id']] = {'state': entry['state'], 'review_path': reports[-1]['path'],
                                         'review_sha256': reports[-1]['sha256'],
                                         'reviewed_utc': entry.get('reviewed_utc'),
                                         'notes': entry.get('notes', ''), 'evidence': entry.get('evidence', [])}
assert len(judgments) == 310
entries = []
for row in matrix['concepts']:
    judgment = judgments[row['concept_id']]
    entries.append({'concept_id': row['concept_id'], 'semantic_fingerprint': semantic_fingerprint(row),
                    'carry_eligible': judgment['state'] != 'REPAIR_HIGH', 'first_pass': judgment})
result = {'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'matrix_sha256': matrix_hash,
          'reports': reports, 'concepts': entries,
          'policy': 'Carry a positive or medium judgment only when the current semantic fingerprint is identical. A repaired HIGH requires a new bound judgment and its own lane warm recheck. Render links, timestamps and popularity snapshots are excluded from this fingerprint.'}
(BASE / 'first-pass-semantic-baseline.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'concepts': len(entries), 'carry_eligible': sum(row['carry_eligible'] for row in entries),
                  'states': dict(collections.Counter(judgment['state'] for judgment in judgments.values()))}))
