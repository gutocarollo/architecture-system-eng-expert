"""Require an explicit, current judgment before a positive author status.

An explicit author judgment is necessary in addition to structural receipts. This
gate binds that judgment to the selected code and prose. It cannot decide whether
an excerpt actually implements a concept; independent semantic review remains a
separate requirement.
"""
import hashlib
import json
import re
import copy
from pathlib import Path
from semantic_fingerprints import semantic_fingerprint, mechanism_fingerprint

_REVIEW_CACHE = {}


def digest(contents):
    return hashlib.sha256(contents).hexdigest()


def canonical_url(url):
    return url.split('#', 1)[0]


def source_lookup(sources):
    output = {}
    for original, source in sources.items():
        output[canonical_url(original)] = source
        output[canonical_url(source.get('url', original))] = source
    for original, source in sources.items():
        if canonical_url(original) == canonical_url(source.get('url', original)):
            output[canonical_url(original)] = source
    return output


def selection_fingerprint(concept_id, selection, sources):
    lookup = source_lookup(sources)
    bindings = []
    for role in ['base', 'application']:
        for url in selection[role + '_urls']:
            source = lookup.get(canonical_url(url), {})
            bindings.append({'role': role, 'url': source.get('url', url),
                             'revision': source.get('revision'), 'sha256': source.get('sha256'),
                             'license': {key: source.get('source_license', {}).get(key)
                                         for key in ['status', 'license_spdx', 'license_expression',
                                                     'url', 'revision', 'path', 'sha256']}})
    payload = {'concept_id': concept_id, 'application_kind': selection.get('application_kind'),
               'mechanism': selection.get('mechanism'), 'limits': selection.get('limits'),
               'decision_evidence': selection.get('decision_evidence', []),
               'sources': sorted(bindings, key=lambda row: (row['role'], row['url']))}
    return digest(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())


def adjudication_issues(concept_id, selection, sources, adjudication, root):
    issues = []

    def fail(kind, reason):
        issues.append({'kind': kind, 'reason': reason})

    if not adjudication:
        fail('AUTHOR_ADJUDICATION_MISSING', 'An explicit current author judgment is required.')
        return issues
    if adjudication.get('concept_id') != concept_id:
        fail('AUTHOR_ADJUDICATION_CONCEPT', 'The judgment names another concept.')
    if adjudication.get('decision') != 'AUTHOR_SOURCE_MATCH':
        fail('AUTHOR_ADJUDICATION_PENDING', 'The author has not positively adjudicated this concept.')
    if adjudication.get('remaining_gates') != []:
        fail('AUTHOR_ADJUDICATION_OPEN_GATE', 'An unresolved author gate prevents a positive status.')
    if not adjudication.get('basis', '').strip():
        fail('AUTHOR_ADJUDICATION_BASIS', 'The mechanism judgment must state its reasoning.')
    if not adjudication.get('checked_at_utc') or not adjudication.get('checked_by'):
        fail('AUTHOR_ADJUDICATION_PROVENANCE', 'The author and time of the judgment are required.')
    expected = selection_fingerprint(concept_id, selection, sources)
    if adjudication.get('selection_fingerprint') != expected:
        fail('AUTHOR_ADJUDICATION_STALE', 'Sources or mechanism/limits changed after the judgment.')
    lookup = source_lookup(sources)
    selected = {role: {canonical_url(lookup.get(canonical_url(url), {}).get('url', url))
                       for url in selection[role + '_urls']}
                for role in ['base', 'application']}
    supported_roles = set()
    for evidence in adjudication.get('primary_evidence', []):
        role = evidence.get('role')
        url = canonical_url(evidence.get('source_url', ''))
        if role not in selected or url not in selected[role]:
            fail('AUTHOR_EVIDENCE_NOT_SELECTED', 'An excerpt does not belong to the selected role/source.')
            continue
        source = lookup.get(url, {})
        if not re.fullmatch(r'[0-9a-f]{40}', source.get('revision') or ''):
            fail('AUTHOR_EVIDENCE_UNPINNED', 'The excerpt must bind an immutable repository revision.')
            continue
        if evidence.get('source_sha256') != source.get('sha256'):
            fail('AUTHOR_EVIDENCE_SOURCE_HASH', 'The excerpt refers to different source bytes.')
            continue
        artifact = Path(root) / source.get('artifact', '__missing__')
        if not artifact.is_file() or digest(artifact.read_bytes()) != source.get('sha256'):
            fail('AUTHOR_EVIDENCE_ARTIFACT', 'The selected source artifact is missing or changed.')
            continue
        lines = artifact.read_text().splitlines()
        start, end = evidence.get('start_line', 0), evidence.get('end_line', 0)
        if not isinstance(start, int) or not isinstance(end, int) or not 1 <= start <= end <= len(lines):
            fail('AUTHOR_EVIDENCE_LINES', 'The selected source span is invalid.')
            continue
        excerpt = '\n'.join(lines[start - 1:end])
        if not excerpt.strip() or digest(excerpt.encode()) != evidence.get('excerpt_sha256'):
            fail('AUTHOR_EVIDENCE_EXCERPT', 'The recorded excerpt differs from the selected source span.')
            continue
        if not evidence.get('claim', '').strip():
            fail('AUTHOR_EVIDENCE_CLAIM', 'The excerpt must state which mechanism step it supports.')
            continue
        supported_roles.add(role)
    for role in ['base', 'application']:
        if role not in supported_roles:
            fail('AUTHOR_EVIDENCE_ROLE_MISSING', 'There is no bound primary excerpt for ' + role + '.')
    return issues


def carry_forward_issues(row, baseline, root):
    """Carry a real non-HIGH first-pass judgment only while its meaning is unchanged."""
    if not baseline or baseline.get('carry_eligible') is not True:
        return [{'kind': 'CURRENT_JUDGMENT_MISSING', 'reason': 'This concept requires a new author adjudication.'}]
    if baseline.get('semantic_fingerprint') != semantic_fingerprint(row):
        return [{'kind': 'REVIEWED_SEMANTICS_CHANGED', 'reason': 'The prior review cannot approve changed meaning-bearing fields.'}]
    review = baseline['first_pass']
    if review.get('state') not in ['APPROVED', 'APPROVED_BOUNDED', 'APPROVED_WITH_MEDIUM', 'MEDIUM_BACKLOG']:
        return [{'kind': 'FIRST_PASS_NOT_POSITIVE', 'reason': 'Only an explicitly accepted bounded mechanism can be carried.'}]
    path = Path(root) / review.get('review_path', '__missing__')
    if not path.is_file() or digest(path.read_bytes()) != review.get('review_sha256'):
        return [{'kind': 'FIRST_PASS_RECEIPT_CHANGED', 'reason': 'The saved independent review receipt is missing or changed.'}]
    return []


def independent_decision_issues(row, decision, root):
    """Bind a real review to unchanged mechanisms and explicit license-only corrections."""
    if not decision or decision.get('concept_id') != row['concept_id']:
        return [{'kind': 'INDEPENDENT_DECISION_MISSING', 'reason': 'No actual concept judgment is bound.'}]
    accepted = {'APPROVED', 'APPROVED_BOUNDED', 'APPROVED_WITH_MEDIUM', 'MEDIUM_BACKLOG'}
    path = Path(root) / decision.get('review_path', '__missing__')
    if not path.is_file() or digest(path.read_bytes()) != decision.get('review_sha256'):
        return [{'kind': 'INDEPENDENT_RECEIPT_CHANGED', 'reason': 'The independent report is missing or changed.'}]
    key = (str(path), decision['review_sha256'])
    if key not in _REVIEW_CACHE:
        report = json.loads(path.read_text())
        _REVIEW_CACHE[key] = (report, {entry['concept_id']: entry for entry in report['concepts']})
    report, concepts = _REVIEW_CACHE[key]
    actual = concepts.get(row['concept_id'], {})
    if (report.get('model') != 'gpt-6.1-sol' or actual.get('state') not in accepted
            or actual.get('state') != decision.get('state')):
        return [{'kind': 'INDEPENDENT_NOT_ACCEPTED', 'reason': 'The report does not contain the claimed accepted judgment.'}]
    if mechanism_fingerprint(row) != decision.get('mechanism_fingerprint'):
        return [{'kind': 'REVIEWED_MECHANISM_CHANGED', 'reason': 'Code, mechanism, limits or skill scope changed after review.'}]
    current = semantic_fingerprint(row)
    if current != decision.get('expected_final_semantic_fingerprint'):
        return [{'kind': 'REVIEWED_METADATA_CHANGED', 'reason': 'The current metadata differs from the explicitly closed version.'}]
    if current == decision.get('reviewed_semantic_fingerprint'):
        return []
    correction = decision.get('license_metadata_correction', {})
    path = Path(root) / correction.get('path', '__missing__')
    if not path.is_file() or digest(path.read_bytes()) != correction.get('sha256'):
        return [{'kind': 'LICENSE_CORRECTION_RECEIPT', 'reason': 'The authorized metadata correction receipt is missing or changed.'}]
    manifest = json.loads(path.read_text())
    changes = [item for item in manifest['changes'] if item['concept_id'] == row['concept_id']]
    restored = copy.deepcopy(row)
    for change in changes:
        before, after = change['before'], change['after']
        unchanged = {k: v for k, v in before.items() if k != 'license_spdx'} == {k: v for k, v in after.items() if k != 'license_spdx'}
        allowed = (((before.get('license_spdx'), after.get('license_spdx')) == ('PostgreSQL', 'Python-2.0')
                    and change['source_url'].startswith('https://github.com/python/cpython/blob/')
                    and change['path'].startswith('Lib/'))
                   or ((before.get('license_spdx'), after.get('license_spdx')) == ('MIT', 'CC-BY-SA-4.0')
                       and change['source_url'].startswith('https://github.com/gitlabhq/gitlabhq/blob/')
                       and change['path'] == 'doc/development/database/multiple_databases.md'))
        source = next((item for item in restored[change['role']] if item['url'] == change['source_url']), None)
        current_license = ({key: source['license'].get(key) for key in after} if source is not None else {})
        if not unchanged or not allowed or source is None or current_license != after:
            return [{'kind': 'LICENSE_CORRECTION_SCOPE', 'reason': 'A metadata exception exceeds its verified source and field scope.'}]
        source['license'] = before
    if not changes or semantic_fingerprint(restored) != decision.get('reviewed_semantic_fingerprint'):
        return [{'kind': 'LICENSE_CORRECTION_NOT_ONLY_DELTA', 'reason': 'The license correction does not reconstruct the reviewed meaning exactly.'}]
    return []
