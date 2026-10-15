"""Upload a verified Nextra release through the protected Sites administration route."""
import argparse
import concurrent.futures
import hashlib
import json
import random
import sys
import termios
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from keychain_secrets import load_values

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
ASSETS = ROOT / 'sites/architecture-course/out'


def read_private_input():
    previous = None
    if sys.stdin.isatty():
        previous = termios.tcgetattr(sys.stdin.fileno())
        changed = previous.copy()
        changed[3] &= ~termios.ECHO
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, changed)
    try:
        print('Ready for private Site access JSON on stdin (input is hidden).', flush=True)
        return json.loads(sys.stdin.readline())
    finally:
        if previous is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, previous)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--private-service-access', action='store_true')
    parser.add_argument('--workers', type=int, default=12)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    target = urllib.parse.urlsplit(args.base_url)
    identity = json.loads((BASE / 'site-identity.json').read_text())
    expected = urllib.parse.urlsplit(identity['expected_url'])
    if target.scheme != 'https' or target.netloc != expected.netloc or target.path not in ('', '/'):
        raise SystemExit('The upload destination must be the registered Site origin.')
    private = read_private_input() if args.private_service_access else {}
    service_token = private.get('service_access_token')
    if args.private_service_access and not isinstance(service_token, str):
        raise SystemExit('The private Site service credential is required.')
    secrets = load_values()
    manifest_path = BASE / 'asset-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    release = manifest['release_id']
    canonical = json.dumps(manifest['files'], sort_keys=True, separators=(',', ':')).encode()
    if hashlib.sha256(canonical).hexdigest() != release:
        raise SystemExit('The release does not match the asset manifest.')

    def upload(item):
        source = (ASSETS / item['path']).resolve()
        if not source.is_relative_to(ASSETS.resolve()) or not source.is_file():
            raise RuntimeError('Invalid local asset path')
        data = source.read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise RuntimeError('An asset changed after manifest creation')
        query = urllib.parse.urlencode(dict(release=release, path=item['path']))
        headers = {'Authorization': 'Bearer ' + secrets['COURSE_UPLOAD_SECRET'],
                   'X-Asset-Sha256': item['sha256'], 'X-Asset-Content-Type': item['content_type'],
                   'Content-Length': str(len(data)), 'Content-Type': 'application/octet-stream'}
        if service_token:
            headers['OAI-Sites-Authorization'] = 'Bearer ' + service_token
        endpoint = args.base_url.rstrip('/') + '/_admin/assets?' + query
        for attempt in range(1, 4):
            request = urllib.request.Request(endpoint, data=data, headers=headers, method='PUT')
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    if response.status != 204:
                        raise RuntimeError('The Site did not acknowledge R2 storage')
                    return dict(path=item['path'], status=response.status, requested_sha256=item['sha256'],
                                checksum_contract='R2 put receives the SHA-256 condition; live read-back is a separate phase.', attempts=attempt)
            except urllib.error.HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    detail = error.read(512).decode(errors='replace')
                    for value in [*secrets.values(), service_token or '']:
                        if value:
                            detail = detail.replace(value, '[redacted]')
                    raise RuntimeError(f'Asset upload HTTP {error.code}: {detail}') from None
            except urllib.error.URLError:
                if attempt == 3:
                    raise RuntimeError('Asset upload network failure') from None
            time.sleep(min(2 ** attempt, 8) + random.random())
        raise RuntimeError('Asset retry budget exhausted')

    results = []
    if args.resume and (BASE / 'upload-receipt.json').exists():
        prior = json.loads((BASE / 'upload-receipt.json').read_text())
        if prior['release_id'] != release or prior['base_url'] != args.base_url or prior['manifest_sha256'] != hashlib.sha256(manifest_path.read_bytes()).hexdigest():
            raise SystemExit('The prior upload receipt is for another release, origin or manifest.')
        expected_hashes = {item['path']: item['sha256'] for item in manifest['files']}
        for result in prior['results']:
            if result['status'] != 204 or result['requested_sha256'] != expected_hashes.get(result['path']):
                raise SystemExit('The prior upload acknowledgment is incompatible with this manifest.')
        results = prior['results']
    acknowledged = {result['path'] for result in results}
    if len(acknowledged) != len(results):
        raise SystemExit('Duplicate prior upload acknowledgments.')
    failures = []
    started = datetime.now(timezone.utc).isoformat()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 16)))
    pending = {executor.submit(upload, item): item['path'] for item in manifest['files'] if item['path'] not in acknowledged}
    try:
        for future in concurrent.futures.as_completed(pending):
            try:
                results.append(future.result())
                if len(results) % 100 == 0:
                    print(json.dumps(dict(uploaded=len(results), total=len(manifest['files']))), flush=True)
            except Exception as error:
                failures.append(dict(path=pending[future], error=str(error)))
                for queued in pending:
                    queued.cancel()
                break
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
    receipt = dict(started_at=started, observed_at=datetime.now(timezone.utc).isoformat(),
                   base_url=args.base_url, release_id=release,
                   manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                   expected_files=len(manifest['files']), uploaded_files=len(results), failures=failures,
                   native_service_access_used=bool(service_token), results=sorted(results, key=lambda x: x['path']),
                   verdict='PASS' if not failures and len(results) == len(manifest['files']) else 'FAIL')
    (BASE / 'upload-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['verdict', 'expected_files', 'uploaded_files', 'failures']}))
    return 0 if receipt['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
