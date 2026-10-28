"""Bind review decisions to meaning-bearing fields, excluding render/run metadata."""
import hashlib
import json


def semantic_payload(row):
    def source(item):
        output = {key: item.get(key) for key in ['repo', 'path', 'revision', 'sha256']}
        output['license'] = {key: item.get('license', {}).get(key)
                             for key in ['status', 'license_spdx', 'license_expression', 'url', 'revision', 'path']}
        return output
    return {'concept_id': row['concept_id'], 'canonical_name': row['canonical_name'],
            'base': [source(item) for item in row['base']],
            'application': [source(item) for item in row['application']],
            'application_kind': row['application_kind'], 'mechanism': row['mechanism'],
            'limits': row['limits'], 'decision_evidence': row.get('decision_evidence', []),
            'skill': {key: row['skill'].get(key) for key in ['repo', 'path', 'revision', 'sha256', 'scope']}}


def semantic_fingerprint(row):
    return hashlib.sha256(json.dumps(semantic_payload(row), sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def mechanism_fingerprint(row):
    """Keep code and meaning fixed while reporting license-label corrections separately."""
    payload = semantic_payload(row)
    for role in ['base', 'application']:
        for item in payload[role]:
            item.pop('license')
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()
