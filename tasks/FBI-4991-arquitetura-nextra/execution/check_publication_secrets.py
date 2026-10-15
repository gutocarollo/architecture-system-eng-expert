"""Scan the staged delivery; baseline only recomputed typed file hashes."""
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
    if finding['RuleID']!='generic-api-key' or not path.endswith('.json'):
        unexplained.append(finding);continue
    staged=subprocess.check_output(['git','show',':'+path],cwd=ROOT,text=True)
    line=staged.splitlines()[finding['StartLine']-1]
    match=re.fullmatch(r'\s*"([^\"]+)"\s*:\s*"([0-9a-f]{64})",?\s*',line)
    if not match:
        unexplained.append(finding);continue
    source_path,expected=match.groups()
    source=(ROOT/source_path).resolve()
    allowed=(ROOT/'labs/architecture').resolve()
    if not source_path.startswith('labs/architecture/') or not source.is_relative_to(allowed) or not source.is_file():
        unexplained.append(finding);continue
    live=hashlib.sha256(source.read_bytes()).hexdigest()
    staged_source=hashlib.sha256(subprocess.check_output(['git','show',':'+source_path],cwd=ROOT)).hexdigest()
    if live!=expected or staged_source!=expected:
        unexplained.append(finding);continue
    validated.append(finding)
    proofs.append(dict(report_path=path,line=finding['StartLine'],source_path=source_path,
                       type='COMPUTED_FILE_SHA256',working_and_staged_source_match=True))
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
