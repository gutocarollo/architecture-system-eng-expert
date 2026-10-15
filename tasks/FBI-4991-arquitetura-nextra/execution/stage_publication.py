"""Stage only the authorized course and the declared sanitized history exports."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--checkpoint',action='store_true');args=parser.parse_args()
manifest=json.loads((BASE/'history/public-export-manifest.json').read_text())
history_root=BASE/'history'
history_allow={str((history_root/entry['path']).relative_to(ROOT)) for entry in manifest['publication_allowlist']}
history_allow.add(str((history_root/'public-export-manifest.json').relative_to(ROOT)))
airflow_manifest=history_root/'airflow/manifest.json'
if airflow_manifest.exists():
    history_allow.add(str(airflow_manifest.relative_to(ROOT)))
    for entry in json.loads(airflow_manifest.read_text())['files']:
        path=airflow_manifest.parent/entry['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']: raise ValueError('Airflow sanitized export changed: '+str(path))
        history_allow.add(str(path.relative_to(ROOT)))
roots=['app','content','docs','scripts','labs','patches','tasks/architecture-course-2026-10-14','tasks/architecture-story-2026-10-14','tasks/FBI-4991-arquitetura-nextra']
root_files=['.gitignore','README.md','mdx-components.jsx','next.config.mjs','package.json','package-lock.json','jsconfig.json','tsconfig.json','next-env.d.ts']
candidates={ROOT/name for name in root_files if (ROOT/name).is_file()}
for name in roots:
    folder=ROOT/name
    if folder.exists(): candidates.update(p for p in folder.rglob('*') if p.is_file() and not p.is_symlink())
selected=[];excluded=[]
for path in sorted(candidates):
    rel=str(path.relative_to(ROOT));reason=None
    if rel==str((BASE/'publication-manifest.json').relative_to(ROOT)): continue
    if '.venv' in path.parts or '__pycache__' in path.parts: continue
    if args.checkpoint and rel.startswith(str((BASE/'curation-repairs').relative_to(ROOT))+'/'): reason='Unfrozen source-repair research remains outside this local checkpoint.'
    if rel.startswith(str(history_root.relative_to(ROOT))+'/') and rel not in history_allow: reason='Private/raw history stays local; only the audited publication allowlist is exported.'
    if rel.startswith('tasks/architecture-course-2026-10-14/evidence/history-'):reason='The sanitized complete replacement is in execution/history/public-index and public-causal.'
    if path.stat().st_size>1_000_000:reason='The repository keeps blobs above 1MB local; a declared compressed or sharded export carries essential evidence.'
    if '-tree.json' in path.name:reason='Repository tree cache, not a publication deliverable.'
    if path.name.startswith('.env'):reason='Local environment configuration.'
    ignored=subprocess.run(['git','check-ignore','-q','--no-index','--',rel],cwd=ROOT).returncode==0
    if ignored: reason=reason or 'Ignored local artifact.'
    if reason:
        excluded.append(dict(path=rel,bytes=path.stat().st_size,reason=reason));continue
    selected.append(dict(path=rel,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
if args.apply:
    head=set(subprocess.check_output(['git','ls-tree','-r','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
    staged=set(subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines())
    dropped=[entry['path'] for entry in excluded if entry['path'] in staged and entry['path'] not in head]
    if dropped:
        working_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in dropped}
        subprocess.run(['git','restore','--staged','--',*dropped],cwd=ROOT,check=True)
        for name,expected in working_hashes.items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected: raise ValueError('An excluded working file changed: '+name)
    for index in range(0,len(selected),100): subprocess.run(['git','add','--',*[e['path'] for e in selected[index:index+100]]],cwd=ROOT,check=True)
report=dict(checkpoint=args.checkpoint,observed_at=datetime.now(timezone.utc).isoformat(),applied=args.apply,selected=selected,excluded_local_artifacts=excluded,
            history_export_manifest='execution/history/public-export-manifest.json',note='Raw local evidence is retained; compressed exports have their own integrity and redaction receipts. Staging does not prove review, publication, merge or deployment.')
output=BASE/'publication-manifest.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if args.apply: subprocess.run(['git','add','--',str(output.relative_to(ROOT))],cwd=ROOT,check=True)
print(json.dumps(dict(applied=args.apply,selected_files=len(selected),selected_bytes=sum(e['bytes'] for e in selected),excluded_files=len(excluded))))
