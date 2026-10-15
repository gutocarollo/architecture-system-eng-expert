"""Scan the staged delivery; baseline only recomputed typed file hashes."""
import ast
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parent
report=BASE/'secrets-current.json'
log=BASE/'secrets-current.log'
command=['gitleaks','git','--staged','--redact=100','--report-format','json','--report-path',str(report)]
first=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
log.write_text(first.stdout+first.stderr)
findings=json.loads(report.read_text())
validated=[];unexplained=[];proofs=[]
for finding in findings:
    path=finding['File']
    if finding['RuleID']!='generic-api-key':
        unexplained.append(finding);continue
    staged=subprocess.check_output(['git','show',':'+path],cwd=ROOT,text=True)
    line=staged.splitlines()[finding['StartLine']-1]
    if path.endswith('/rare-security/assemble_evidence.py'):
        matches=[]
        for node in ast.walk(ast.parse(staged)):
            if isinstance(node,ast.Assign) and node.lineno==finding['StartLine'] and isinstance(node.value,ast.Tuple):
                values=[item.value for item in node.value.elts if isinstance(item,ast.Constant) and isinstance(item.value,str)]
                if len(values)==2 and re.fullmatch(r'[\w.-]+/[\w.-]+',values[0]) and re.fullmatch(r'[0-9a-f]{40}',values[1]): matches.append(values)
        if len(matches)==1:
            repo,revision=matches[0]
            check=subprocess.run(['gh','api',f'repos/{repo}/commits/{revision}','--jq','.sha'],capture_output=True,text=True)
            if check.returncode==0 and check.stdout.strip()==revision:
                validated.append(finding);proofs.append(dict(report_path=path,line=finding['StartLine'],type='PUBLIC_GIT_COMMIT_SHA',repo=repo,github_commit_verified=True));continue
        unexplained.append(finding);continue
    if not path.endswith('.json'):
        unexplained.append(finding);continue
    match=re.fullmatch(r'\s*"([^\"]+)"\s*:\s*"([0-9a-f]{64})",?\s*',line)
    if not match:
        unexplained.append(finding);continue
    source_path,expected=match.groups()
    source=(ROOT/source_path).resolve()
    if not source.is_relative_to(ROOT.resolve()) or not source.is_file():
        unexplained.append(finding);continue
    live=hashlib.sha256(source.read_bytes()).hexdigest()
    current=subprocess.run(['git','show',':'+source_path],cwd=ROOT,capture_output=True)
    if current.returncode==0 and live==expected and hashlib.sha256(current.stdout).hexdigest()==expected:
        validated.append(finding);proofs.append(dict(report_path=path,line=finding['StartLine'],source_path=source_path,type='COMPUTED_FILE_SHA256',working_and_staged_source_match=True));continue
    historical=False
    for revision in ['HEAD','HEAD^']:
        blob=subprocess.run(['git','show',revision+':'+source_path],cwd=ROOT,capture_output=True)
        if blob.returncode==0 and hashlib.sha256(blob.stdout).hexdigest()==expected:
            commit=subprocess.check_output(['git','rev-parse',revision],cwd=ROOT,text=True).strip()
            validated.append(finding);proofs.append(dict(report_path=path,line=finding['StartLine'],source_path=source_path,type='HISTORICAL_FILE_SHA256',git_commit=commit,recomputed_from_git_blob=True));historical=True;break
    if historical:continue
    proof_path=BASE/'curation-repairs/historical-mdx-hash-proof.json'
    if proof_path.exists():
        proof=json.loads(proof_path.read_text())
        snapshot=ROOT/proof.get('historical_document_path','missing')
        if proof.get('document_path')==source_path and proof.get('recomputed_sha256')==expected and snapshot.is_file() and hashlib.sha256(snapshot.read_bytes()).hexdigest()==expected:
            validated.append(finding);proofs.append(dict(report_path=path,line=finding['StartLine'],source_path=source_path,type='RECONSTRUCTED_HISTORICAL_FILE_SHA256',snapshot_path=str(snapshot.relative_to(ROOT)),recomputed_from_snapshot=True));continue
    unexplained.append(finding)
baseline=BASE/'secrets-verified-hash-baseline.json'
baseline.write_text(json.dumps(validated,indent=2)+'\n')
receipt=dict(observed_at=datetime.now(timezone.utc).isoformat(),raw_findings=len(findings),
             recomputed_typed_file_hashes=proofs,unexplained=[dict(file=f['File'],rule=f['RuleID'],line=f['StartLine']) for f in unexplained],
             no_global_scanner_rules_changed=True,scope='Staged plaintext only; decoded compressed history has a separate audited receipt.')
if unexplained:
    receipt['verdict']='FAIL'
else:
    second=subprocess.run(command+['--baseline-path',str(baseline)],cwd=ROOT,text=True,capture_output=True)
    (BASE/'secrets-current-verified.log').write_text(second.stdout+second.stderr)
    receipt.update(verdict='PASS' if second.returncode==0 else 'FAIL',verified_scan_exit=second.returncode)
(BASE/'secrets-publication-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
raise SystemExit(0 if receipt['verdict']=='PASS' else 1)
