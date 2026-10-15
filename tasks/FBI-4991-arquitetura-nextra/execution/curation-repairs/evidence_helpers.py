"""Assemble repair evidence without modifying the frozen curation artifacts."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
SOURCES = json.loads((BASE / 'sources.json').read_text())


def source(repo, path, spans, revision=None):
    candidates = [row for row in SOURCES if row.get('repo') == repo and row.get('path') == path
                  and row.get('http_status') == 200 and (revision is None or row['revision'] == revision)]
    record = dict(candidates[-1])
    lines = (ROOT / record['artifact']).read_text().splitlines()
    record['evidence'] = []
    for start, end, claim in spans:
        assert 1 <= start <= end <= len(lines), (path, start, end, len(lines))
        excerpt = '\n'.join(lines[start - 1:end])
        record['evidence'].append({'start_line': start, 'end_line': end,
                                   'url': record['url'].split('#')[0] + f'#L{start}-L{end}',
                                   'excerpt': excerpt, 'excerpt_sha256': hashlib.sha256(excerpt.encode()).hexdigest(),
                                   'claim': claim})
    licenses = [row for row in SOURCES if row.get('repo') == repo and row.get('revision') == record['revision']
                and (row.get('kind') == 'LICENSE' or row.get('path') in ['LICENSE', 'LICENSE.md', 'LICENSE.txt'])
                and row.get('http_status') == 200]
    license_record = dict(licenses[-1])
    text = (ROOT / license_record['artifact']).read_text()
    spdx = license_record.get('license_spdx')
    if spdx is None:
        if 'Apache License' in text and 'Version 2.0' in text:
            spdx = 'Apache-2.0'
        elif 'GNU AFFERO GENERAL PUBLIC LICENSE' in text and 'Version 3' in text:
            spdx = 'AGPL-3.0'
    assert spdx is not None, (repo, 'license identifier unresolved')
    license_record.update(status='READ', license_spdx=spdx)
    record['license'] = license_record
    return record
