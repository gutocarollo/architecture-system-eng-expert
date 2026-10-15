#!/usr/bin/env python3
"""Restore the exact consolidated author packet after checking both hashes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--force',action='store_true');args=parser.parse_args()
manifest=json.loads((BASE/'publication-manifest.json').read_text())
archive=(BASE/manifest['archive']).read_bytes()
assert hashlib.sha256(archive).hexdigest()==manifest['archive_sha256']
contents=gzip.decompress(archive)
assert hashlib.sha256(contents).hexdigest()==manifest['contents_sha256']
target=BASE/manifest['source']
if target.exists() and target.read_bytes()!=contents and not args.force:
 raise SystemExit('Preserve the different local author packet before using --force.')
target.write_bytes(contents)
print(manifest['source'],manifest['contents_sha256'])
