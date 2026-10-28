#!/usr/bin/env python3
"""Restore and verify the generated matrix from its compact publication artifact."""
import argparse,gzip,hashlib,json
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--force',action='store_true');args=parser.parse_args()
base=Path(__file__).resolve().parent
index=base/'publication-index.json'
records=json.loads(index.read_text()) if index.exists() else [json.loads((base/'matrix.publication.json').read_text())]
for manifest in records:
 archive=(base/manifest['archive']).read_bytes()
 assert hashlib.sha256(archive).hexdigest()==manifest['archive_sha256'],'Archive hash mismatch'
 contents=gzip.decompress(archive)
 assert hashlib.sha256(contents).hexdigest()==manifest['contents_sha256'],'Contents hash mismatch'
 target=base/manifest['source']
 if target.exists() and target.read_bytes()!=contents and not args.force:
  raise SystemExit('The local artifact differs. Preserve it or pass --force to restore the published generated version: '+manifest['source'])
 target.write_bytes(contents)
 print('Artifact restored and verified:',manifest['source'],manifest['contents_sha256'])
