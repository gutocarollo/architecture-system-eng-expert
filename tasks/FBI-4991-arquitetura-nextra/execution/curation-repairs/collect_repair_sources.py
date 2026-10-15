#!/usr/bin/env python3
"""Capture requested primary sources only in the separate repair workspace."""
import concurrent.futures
import datetime
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
FROZEN = BASE.parent / 'curation'
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
requests = json.loads((BASE / sys.argv[1]).read_text())
sources = json.loads((BASE / 'sources.json').read_text())
metadata = json.loads((BASE / 'repository-receipts.json').read_text()) if (BASE / 'repository-receipts.json').exists() else {}
cached_metadata = json.loads((FROZEN / 'github-metadata.json').read_text())
cached_revisions = json.loads((FROZEN / 'revisions.json').read_text())


def api(endpoint):
    result = subprocess.run(['gh', 'api', endpoint], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[:300])
    return json.loads(result.stdout)


for request in requests:
    repo = request['repo']
    if repo not in metadata:
        item = cached_metadata.get(repo)
        if item and 'default_branch' in item:
            metadata[repo] = dict(item)
        else:
            item = api('repos/' + repo)
            metadata[repo] = {'repository': item['full_name'], 'default_branch': item['default_branch'],
                              'stars': item['stargazers_count'], 'license_spdx': (item.get('license') or {}).get('spdx_id'),
                              'observed_utc': now()}
    ref = request.get('ref') or metadata[repo]['default_branch']
    revision_key = repo + '@' + ref
    if not request.get('revision'):
        sha = cached_revisions.get(revision_key, {}).get('sha') or metadata[repo].get('revisions', {}).get(ref)
        if not sha:
            sha = api('repos/' + repo + '/commits/' + ref)['sha']
        metadata[repo].setdefault('revisions', {})[ref] = sha
        request['revision'] = sha
    request['ref'] = ref

targets = [(request['repo'], request['revision']) for request in requests]
for repo, revision in sorted(set(targets)):
    if any(row.get('repo') == repo and row.get('revision') == revision and row.get('kind') == 'LICENSE' for row in sources):
        continue
    cached = json.loads((FROZEN / 'revision-licenses.json').read_text()).get(repo + '@' + revision)
    if cached and cached.get('status') == 'READ':
        item = dict(cached)
        contents = (ROOT / item['artifact']).read_bytes()
        artifact = BASE / 'raw' / ('license-' + hashlib.sha256((repo + '@' + revision).encode()).hexdigest() + '.txt')
        artifact.write_bytes(contents)
        item.update(kind='LICENSE', reused_from=item['artifact'], artifact=str(artifact.relative_to(ROOT)), local_verified_utc=now())
        sources.append(item)
    else:
        try:
            license_record = api('repos/' + repo + '/license?ref=' + revision)
            requests.append({'repo': repo, 'revision': revision, 'ref': revision, 'path': license_record['path'],
                             'kind': 'LICENSE', 'license_spdx': (license_record.get('license') or {}).get('spdx_id')})
        except Exception as error:
            metadata[repo].setdefault('license_errors', []).append({'revision': revision, 'error': str(error), 'observed_utc': now()})


def collect(request):
    repo, revision, source_path = request['repo'], request['revision'], request['path']
    url = f'https://raw.githubusercontent.com/{repo}/{revision}/{source_path}'
    matching = next((row for row in sources if row.get('repo') == repo and row.get('revision') == revision
                     and row.get('path') == source_path and row.get('http_status') == 200), None)
    if matching:
        item = dict(matching)
        for key in ['kind', 'license_spdx']:
            if key in request:
                item[key] = request[key]
        return item
    item = {'repo': repo, 'revision': revision, 'path': source_path,
            'url': f'https://github.com/{repo}/blob/{revision}/{source_path}', 'raw_url': url, 'observed_utc': now()}
    try:
        response = urllib.request.urlopen(url, timeout=40)
        contents = response.read()
        artifact = BASE / 'raw' / (hashlib.sha256(url.encode()).hexdigest() + '.txt')
        artifact.write_bytes(contents)
        item.update(http_status=response.status, sha256=hashlib.sha256(contents).hexdigest(),
                    line_count=len(contents.splitlines()), artifact=str(artifact.relative_to(ROOT)))
        for key in ['kind', 'license_spdx']:
            if key in request:
                item[key] = request[key]
    except Exception as error:
        item['error'] = str(error)
    return item


with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    new_records = list(executor.map(collect, requests))
sources.extend(new_records)
deduplicated = {(row['repo'], row.get('revision'), row['path']): row for row in sources}
(BASE / 'sources.json').write_text(json.dumps(list(deduplicated.values()), ensure_ascii=False, indent=2))
(BASE / 'repository-receipts.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
print(json.dumps({'requested': len(requests), 'captured': sum(row.get('http_status') == 200 for row in new_records),
                  'failures': [{'repo': row['repo'], 'path': row['path'], 'error': row.get('error')} for row in new_records if row.get('http_status') != 200]}))
