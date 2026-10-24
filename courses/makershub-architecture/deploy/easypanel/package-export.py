#!/usr/bin/env python3
"""Freeze the existing export into an isolated, allowlisted Docker context."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--path-only', action='store_true')
arguments = parser.parse_args()
runtime_root = Path(__file__).resolve().parent
repository_root = runtime_root.parent.parent
export_root = repository_root / 'out'
if not (export_root / 'index.html').is_file():
    raise SystemExit('The frozen Nextra export must contain index.html')

entries = []
for source in sorted(export_root.rglob('*')):
    relative = source.relative_to(export_root)
    if source.is_symlink():
        raise SystemExit(f'Symlinks are not allowed in the export: {relative}')
    if any(part.startswith('.') or part == 'node_modules' for part in relative.parts):
        raise SystemExit(f'Hidden or dependency paths are not allowed: {relative}')
    if source.suffix.lower() in {'.pem', '.key', '.p12', '.pfx'}:
        raise SystemExit(f'Credential file types are not allowed: {relative}')
    if source.is_dir():
        continue
    if not source.is_file():
        raise SystemExit(f'Only regular files are allowed: {relative}')
    entries.append((source, relative))

build_root = runtime_root / '.build'
build_root.mkdir(exist_ok=True)
context = Path(tempfile.mkdtemp(prefix='course-', dir=build_root))
try:
    for filename in ('Dockerfile', '.dockerignore', 'package.json', 'package-lock.json', 'app.js', 'server.js'):
        shutil.copyfile(runtime_root / filename, context / filename)
    export_digest = hashlib.sha256()
    byte_count = 0
    page_count = 0
    for source, relative in entries:
        destination = context / 'public' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        payload = destination.read_bytes()
        content_hash = hashlib.sha256(payload).hexdigest()
        export_digest.update(relative.as_posix().encode('utf-8') + b'\0' + content_hash.encode('ascii') + b'\n')
        byte_count += len(payload)
        page_count += relative.suffix == '.html'
    manifest = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'source': 'out',
        'files': len(entries),
        'html_pages': page_count,
        'bytes': byte_count,
        'sha256': export_digest.hexdigest(),
        'source_commit': subprocess.check_output(
            ['git', '-C', str(repository_root), 'rev-parse', 'HEAD'], text=True
        ).strip(),
    }
    (context / 'export-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
except BaseException:
    shutil.rmtree(context)
    raise
print(context if arguments.path_only else json.dumps({'context': str(context), **manifest}))
