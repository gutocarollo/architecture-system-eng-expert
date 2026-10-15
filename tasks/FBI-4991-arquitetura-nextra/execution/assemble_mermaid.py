"""Combine fresh syntax with render receipts for the same immutable diagrams."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
files=[str(p.relative_to(ROOT)) for p in (ROOT/'content').rglob('*.mdx') if '```mermaid' in p.read_text()]
fingerprint=hashlib.sha256(''.join(str(path)+hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sorted(files)).encode()).hexdigest()[:12]
syntax_path=BASE/f'mermaid-syntax-{fingerprint}.json'
if not syntax_path.exists():
    result=subprocess.run(['node','scripts/verify-mermaid.mjs','node_modules/mermaid/dist/mermaid.esm.mjs',*files,'--out',str(syntax_path)],cwd=ROOT,capture_output=True,text=True)
    if result.returncode: raise SystemExit(result.stderr or result.stdout)
syntax=json.loads(syntax_path.read_text())
assert not syntax['errors'] and syntax['status']=='PASS'
previous=[BASE/'mermaid-render-final.json',BASE/'mermaid-pg-cas.json']
if (BASE/'mermaid-airflow-retry.json').exists(): previous.append(BASE/'mermaid-airflow-retry.json')
if (BASE/'mermaid-semantic-repairs.json').exists(): previous.append(BASE/'mermaid-semantic-repairs.json')
renders={}
for path in previous:
    receipt=json.loads(path.read_text())
    for block in receipt['blocks']:
        renders[(block['path'],block['fence_index'],block['source_sha256'])]=block
for block in syntax['blocks']:
    document=Path(block['path'])
    assert hashlib.sha256(document.read_bytes()).hexdigest()==block['document_sha256']
    render=renders[(block['path'],block['fence_index'],block['source_sha256'])]['render']
    assert render['status']=='PASS'
    assert hashlib.sha256(Path(render['artifact_path']).read_bytes()).hexdigest()==render['artifact_sha256']
    block['render']=render
syntax.update(observed_at=datetime.now(timezone.utc).isoformat(),syntax_only=False,status='PASS',
              source_receipts=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [syntax_path,*previous]])
output=BASE/'mermaid-current.json'
output.write_text(json.dumps(syntax,ensure_ascii=False,indent=2)+'\n')
print('Current Mermaid: '+str(len(syntax['blocks']))+' syntax and render receipts verified against current document and image hashes.')
