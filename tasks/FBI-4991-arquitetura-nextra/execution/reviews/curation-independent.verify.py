"""Reproduce the independent frozen-packet integrity and coverage checks."""
import collections
import datetime
import gzip
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REVIEWS = Path(__file__).resolve().parent
CURATION = ROOT / 'tasks/FBI-4991-arquitetura-nextra/execution/curation'
read = lambda path: json.loads(path.read_text())
digest = lambda contents: hashlib.sha256(contents).hexdigest()
sources = read(CURATION / 'sources.json')
licenses = read(CURATION / 'revision-licenses.json')
selections = read(CURATION / 'source-selections.json')
skills = read(CURATION / 'skill-candidates.json')
matrix = read(CURATION / 'matrix.json')
freeze = read(CURATION / 'freeze-receipt.json')
assignment = set(read(REVIEWS / 'curation-assignment-one.json')['concept_ids'])
judgments = read(REVIEWS / 'curation-independent.assignment-one.json')
errors = []


def verify_record(record):
    artifact = ROOT / record['artifact']
    if not artifact.is_file():
        return ['missing', record['artifact']]
    if digest(artifact.read_bytes()) != record['sha256']:
        return ['hash', record['artifact']]
    return None


historical = [record for record in sources.values()
              if record.get('http_status') == 200 and record.get('artifact')]
for record in historical:
    failure = verify_record(record)
    if failure:
        errors.append(failure)

active = {url for row in selections.values()
          for role in ['base_urls', 'application_urls'] for url in row[role]}
active.update(row['url'] for row in skills.values())
active_licenses = set()
for url in active:
    source = sources[url]
    key = source['repo'] + '@' + source['revision']
    active_licenses.add(key)
    record = licenses[key]
    failure = verify_record(record)
    if record['status'] != 'READ' or failure:
        errors.append(['license', key, failure])

publications = []
for publication in read(CURATION / 'publication-index.json'):
    archive = (CURATION / publication['archive']).read_bytes()
    contents = gzip.decompress(archive)
    verified = (digest(archive) == publication['archive_sha256']
                and digest(contents) == publication['contents_sha256']
                and contents == (CURATION / publication['source']).read_bytes())
    publications.append({'archive': publication['archive'], 'verified': verified,
                         'sha256': digest(archive), 'contents_sha256': digest(contents)})
    if not verified:
        errors.append(['publication', publication['archive']])

matrix_hash = digest((CURATION / 'matrix.json').read_bytes())
if matrix_hash != freeze['active_validation']['matrix_sha256']:
    errors.append(['freeze_changed', matrix_hash])
ids = [row['concept_id'] for row in judgments['concepts']]
if len(ids) != 183 or set(ids) != assignment or len(ids) != len(set(ids)):
    errors.append(['assignment_mismatch'])
if any(row['state'] == 'UNREVIEWED' for row in judgments['concepts']):
    errors.append(['unfinished_assigned_semantics'])

catalog_occurrences = []
for file in (ROOT / 'content/referencia/catalogo').glob('*.mdx'):
    catalog_occurrences.extend(re.findall(r'current-curation:([^ *}]+)', file.read_text()))
priorities = read(CURATION / 'priority-reconciliation.json')['priority_entries']
priority_text = (ROOT / 'content/referencia/prioritarios.mdx').read_text()
missing_priority_urls = [url for row in priorities for url in row['concept_reference_urls']
                         if url not in priority_text]
if missing_priority_urls:
    errors.append(['priority_links', missing_priority_urls])

# Mutate the expected digest only in memory and use the same verification path.
mutant = {**historical[0], 'sha256': '0' * 64}
mutation_rejected = verify_record(mutant) is not None
if not mutation_rejected:
    errors.append(['mutation_not_rejected'])

receipt = {
    'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'workspace': str(ROOT), 'matrix_sha256': matrix_hash,
    'historical_http200_records': len(historical),
    'historical_unique_source_artifacts': len({row['artifact'] for row in historical}),
    'active_locators': len(active), 'active_license_revisions': len(active_licenses),
    'publications': publications,
    'canonical_concepts': len(matrix['concepts']),
    'catalog_occurrences': len(catalog_occurrences),
    'catalog_unique_concepts': len(set(catalog_occurrences)),
    'priority_entries': len(priorities),
    'priority_links': sum(len(row['concept_reference_urls']) for row in priorities),
    'assigned_concepts': len(ids),
    'assigned_states': dict(collections.Counter(row['state'] for row in judgments['concepts'])),
    'other_lane_concepts': 127,
    'mutation_expected_hash_corruption': 'REJECTED' if mutation_rejected else 'MISSED',
    'errors': errors,
    'verdict': 'PASS' if not errors else 'FAIL',
    'boundary': 'Integrity PASS does not override semantic REPAIR or approve the other lane.'
}
(REVIEWS / 'curation-independent.final-receipt.json').write_text(
    json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False))
raise SystemExit(bool(errors))
