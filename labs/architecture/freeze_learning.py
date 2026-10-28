"""Freeze only the author's 15-case slice, preserving root-owned Postgres paths."""
import hashlib
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning'
RESERVED={'query-grain-postgres','revision-cas-postgres'}
files=[]
for relative in ['content/jornadas','content/explicacoes/casos','content/tutoriais/casos','content/guias/casos']:
    files.extend(p for p in (ROOT/relative).rglob('*') if p.is_file() and not any(name in p.parts for name in RESERVED))
files.extend(ROOT/p for p in ['content/explicacoes/_meta.js','content/tutoriais/_meta.js','content/guias/_meta.js','content/explicacoes/read-models/index.mdx'])
files.extend(p for p in (ROOT/'labs/architecture').rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.venv' not in p.parts)
files.extend(BASE/name for name in ['concept-matrix.json','additional-observations.json'])
registry=json.loads((BASE/'families.json').read_text())
owned=[c for c in registry['families'] if c['case_id'] not in RESERVED]
manifest={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'workspace':str(ROOT),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'base_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'scope':'Owned learning cases and architecture labs. Reserved Postgres case paths and the disposable SDK environment are excluded. The shared registry is bound by its owned subset.','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))},'owned_registry_sha256':hashlib.sha256(json.dumps(owned,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'independent_review':'PENDING_WARM_RECHECK_T1_T2_T3'}
output=BASE/'owned-hashes.json';output.write_text(json.dumps(manifest,indent=2)+'\n')
print(f'freeze_files={len(manifest["files"])} observed_at_utc={manifest["recorded_at_utc"]} manifest_sha256={hashlib.sha256(output.read_bytes()).hexdigest()}')
