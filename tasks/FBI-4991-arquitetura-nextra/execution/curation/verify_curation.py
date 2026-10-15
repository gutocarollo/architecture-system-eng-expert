#!/usr/bin/env python3
"""Check source integrity independently of semantic and review completion."""
import argparse
import collections
import datetime
import gzip
import hashlib
import json
import re
from pathlib import Path
from adjudication_gate import adjudication_issues, carry_forward_issues, independent_decision_issues

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--require-complete', action='store_true')
parser.add_argument('--require-independent', action='store_true')
args = parser.parse_args()
read = lambda name: json.loads((BASE / name).read_text())
digest = lambda contents: hashlib.sha256(contents).hexdigest()
coverage = json.loads((ROOT / 'tasks/architecture-course-2026-10-14/evidence/coverage.json').read_text())
matrix = read('matrix.json')
sources = read('sources.json')
selections = read('source-selections.json')
skills = read('skill-candidates.json')
licenses = read('revision-licenses.json')
adjudications = read('author-adjudications.json')
review_baseline = {row['concept_id']: row for row in read('review-baseline.json')['concepts']}
closure_path = BASE.parent / 'curation-repairs/independent-closure.json'
closure = json.loads(closure_path.read_text()) if closure_path.exists() else {}
closure_by_id = {row['concept_id']: row for row in closure.get('concepts', [])}
errors = []

def require(condition, kind, **detail):
    if not condition:
        errors.append({'kind': kind, **detail})

expected = {row['concept_id'] for row in coverage['concepts']}
actual = [row['concept_id'] for row in matrix['concepts']]
require(len(expected) == 310 and set(actual) == expected and len(actual) == len(set(actual)), 'CANONICAL_IDS')
require(set(selections) == expected, 'SELECTION_IDS')
require(len(coverage['priority_entries']) == 40, 'PRIORITY_COUNT')
for priority in coverage['priority_entries']:
    require(set(priority['concept_ids']).issubset(expected), 'PRIORITY_CONCEPT', priority_id=priority['priority_id'])
catalog_reconciliation = read('catalog-reconciliation.json')
require(catalog_reconciliation['unique_concepts_linked'] == 310 and not catalog_reconciliation['concepts_without_catalog_link'], 'CATALOG_RECONCILIATION')
priority_reconciliation = read('priority-reconciliation.json')
require(len(priority_reconciliation['priority_entries']) == 40, 'PRIORITY_RECONCILIATION')
for priority in priority_reconciliation['priority_entries']:
    original = next(row for row in coverage['priority_entries'] if row['priority_id'] == priority['priority_id'])
    require(priority['concept_ids'] == original['concept_ids'], 'PRIORITY_MEMBERSHIPS', priority_id=priority['priority_id'])
active = {url for row in selections.values() for key in ['base_urls', 'application_urls'] for url in row[key]}
active.update(row['url'] for row in skills.values())
checked_sources = set()
checked_licenses = set()
for url in sorted(active):
    source = sources.get(url, {})
    require(bool(source), 'SOURCE_RECORD', url=url)
    require(bool(re.fullmatch(r'[0-9a-f]{40}', source.get('revision') or '')), 'SOURCE_REVISION', url=url)
    if source.get('kind') == 'FILE':
        require(source.get('http_status') == 200, 'SOURCE_HTTP', url=url, status=source.get('http_status'))
        artifact = ROOT / source.get('artifact', '__missing__')
        require(artifact.is_file(), 'SOURCE_ARTIFACT', url=url)
        if artifact.is_file():
            require(digest(artifact.read_bytes()) == source.get('sha256'), 'SOURCE_HASH', url=url)
            checked_sources.add(str(artifact))
    key = source.get('repo', '') + '@' + source.get('revision', '')
    license_record = source.get('source_license') or licenses.get(key, {})
    require(license_record.get('status') == 'READ', 'LICENSE_READ', url=url, license_key=key)
    require(license_record.get('revision') == source.get('revision'), 'LICENSE_REVISION', url=url)
    if license_record.get('status') == 'READ':
        artifact = ROOT / license_record.get('artifact', '__missing__')
        require(artifact.is_file(), 'LICENSE_ARTIFACT', license_key=key)
        if artifact.is_file():
            require(digest(artifact.read_bytes()) == license_record.get('sha256'), 'LICENSE_HASH', license_key=key)
            checked_licenses.add(key)
for row in matrix['concepts']:
    require(bool(row['base']) and bool(row['application']) and bool(row['skill']), 'ROLES', concept_id=row['concept_id'])
    require(bool(row['mechanism'].strip()) and bool(row['limits'].strip()), 'AUTHOR_FINDING', concept_id=row['concept_id'])
    require(row.get('not_applicable') is False, 'EXEMPTION', concept_id=row['concept_id'])
    require(bool(row.get('learning')), 'LEARNING_MAPPING', concept_id=row['concept_id'])
    require(any(item['role'] == 'application' and item['hits'] for item in row['source_evidence']), 'APPLICATION_LOCATOR', concept_id=row['concept_id'])
    judgment = adjudications.get(row['concept_id'])
    judgment_errors = (adjudication_issues(row['concept_id'], selections[row['concept_id']], sources, judgment, ROOT)
                       if judgment else (independent_decision_issues(row, closure_by_id[row['concept_id']], ROOT)
                                         if row['concept_id'] in closure_by_id else carry_forward_issues(row, review_baseline.get(row['concept_id']), ROOT)))
    require(not judgment_errors, 'CURRENT_POSITIVE_JUDGMENT', concept_id=row['concept_id'], details=judgment_errors)
    if row['concept_id'] in closure_by_id:
        independent_errors = independent_decision_issues(row, closure_by_id[row['concept_id']], ROOT)
        require(not independent_errors, 'BOUND_INDEPENDENT_DECISION', concept_id=row['concept_id'], details=independent_errors)
for publication in read('publication-index.json'):
    archive = (BASE / publication['archive']).read_bytes()
    contents = gzip.decompress(archive)
    require(digest(archive) == publication['archive_sha256'], 'ARCHIVE_HASH', archive=publication['archive'])
    require(digest(contents) == publication['contents_sha256'], 'CONTENTS_HASH', archive=publication['archive'])
    require(contents == (BASE / publication['source']).read_bytes(), 'ARCHIVE_ROUNDTRIP', archive=publication['archive'])
    require(len(archive) <= 1_000_000, 'ARCHIVE_SIZE_POLICY', archive=publication['archive'], bytes=len(archive))
pending = [row['concept_id'] for row in matrix['concepts'] if row['status'] != 'AUTHOR_SOURCE_MATCH']
accepted_states = {'APPROVED', 'APPROVED_BOUNDED', 'APPROVED_WITH_MEDIUM', 'MEDIUM_BACKLOG'}
independent = [row['concept_id'] for row in matrix['concepts'] if row['independent_review'] not in accepted_states]
structural_error_count = len(errors)
if args.require_complete:
    require(not pending, 'SEMANTIC_COMPLETION', pending=pending)
if args.require_independent:
    require(not independent, 'INDEPENDENT_COMPLETION', pending_count=len(independent))
    require(set(closure_by_id) == expected and closure.get('unresolved_high') == 0, 'INDEPENDENT_REPORT_COVERAGE')
    require(closure.get('final_matrix_sha256') == digest((BASE / 'matrix.json').read_bytes()), 'INDEPENDENT_FINAL_MATRIX_BINDING')
receipt = {'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': str(ROOT), 'canonical_concepts': len(actual), 'priority_entries': len(coverage['priority_entries']), 'active_source_locators': len(active), 'source_artifacts_checked': len(checked_sources), 'license_revisions_checked': len(checked_licenses), 'matrix_sha256': digest((BASE / 'matrix.json').read_bytes()), 'structural_integrity': 'PASS' if structural_error_count == 0 else 'FAIL', 'requested_gate': 'PASS' if not errors else 'FAIL', 'semantic_pending': pending, 'independent_pending_count': len(independent), 'errors_by_kind': dict(collections.Counter(error['kind'] for error in errors)), 'errors': errors, 'note': 'Integrity, HTTP status and lexical locators do not establish semantic correctness or independent approval.'}
(BASE / 'curation-validation.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: value for key, value in receipt.items() if key not in ['errors', 'note']}, ensure_ascii=False))
raise SystemExit(1 if errors else 0)
