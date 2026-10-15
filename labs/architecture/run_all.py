"""Run isolated labs and write checkable receipts for the current source bytes."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LAB_ROOT=ROOT/'labs/architecture'
CASES=['single-flight-cancel','early-refresh','date-only','opportunity-entry',
       'order-boundaries','order-delivery','reservation','consensus','queue-workflow',
       'cache-policy','ledger-projection','storage-partitions','safe-release','access-policy','diagnostics']


def command(case):
    if case=='date-only': return ['node',str(LAB_ROOT/case/'run.mjs')]
    if case in CASES[:4]: return ['python3',str(LAB_ROOT/case/'run.py')]
    return ['python3',str(LAB_ROOT/'financial.py'),case]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='tasks/FBI-4991-arquitetura-nextra/execution/learning/receipts.json')
    args=parser.parse_args()
    receipts=[]
    for case in CASES+['object-patterns']:
        cmd=command(case) if case!='object-patterns' else ['python3',str(LAB_ROOT/'object_patterns.py')]
        env={**os.environ,'TZ':'America/Sao_Paulo'}
        started=datetime.now(timezone.utc).isoformat()
        result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=30)
        record=dict(case_id=case,observed_at_utc=started,command=cmd,
            environment={'TZ':'America/Sao_Paulo','python':platform.python_version(),'node':subprocess.check_output(['node','--version'],text=True).strip()},
            exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,
            scope='LOCAL_LEARNING_WITH_SYNTHETIC_INPUTS')
        if case in CASES[:4]:
            record['historical_sources']=json.loads((LAB_ROOT/case/'manifest.json').read_text())
        receipts.append(record)
        print(f'case={case} exit={result.returncode} stdout_lines={len(result.stdout.splitlines())}')
    hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in LAB_ROOT.rglob('*') if path.is_file() and '__pycache__' not in str(path) and '.venv' not in path.parts}
    data=dict(schema_version=1,workspace=str(ROOT),base_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              receipts=receipts,source_sha256=hashes,
              verdict='PASS' if all(r['exit_code']==0 for r in receipts) else 'FAIL',
              independent_review='PENDING',production_execution=False)
    output=ROOT/args.out;output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(0 if data['verdict']=='PASS' else 1)

if __name__=='__main__': main()
