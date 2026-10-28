"""Verify that a learner can repair a disposable candidate with the historical diff."""
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LAB=ROOT/'labs/architecture'
receipts=[]
for case in ['single-flight-cancel','date-only']:
    with tempfile.TemporaryDirectory(prefix=f'{case}-candidate-') as directory:
        candidate=Path(directory)/('candidate.py' if case=='single-flight-cancel' else 'candidate.ts')
        original=LAB/case/('before.py' if case=='single-flight-cancel' else 'candidate-before.ts')
        diff=LAB/case/('source.diff' if case=='single-flight-cancel' else 'candidate.patch')
        shutil.copyfile(original,candidate)
        command=(['python3',str(LAB/case/'run.py')] if case=='single-flight-cancel' else ['node',str(LAB/case/'run.mjs')])+['--candidate',str(candidate)]
        env={**os.environ,'TZ':'America/Sao_Paulo'}
        before=subprocess.run(command,env=env,capture_output=True,text=True)
        patched=subprocess.run(['patch',str(candidate)],input=diff.read_text(),capture_output=True,text=True)
        after=subprocess.run(command,env=env,capture_output=True,text=True)
        assert before.returncode!=0,(case,'the unprotected candidate must fail the corrected contract')
        assert patched.returncode==0,(case,patched.stderr)
        assert after.returncode==0,(case,after.stderr)
        receipts.append(dict(case_id=case,observed_at_utc=datetime.now(timezone.utc).isoformat(),
            command=command,before_exit=before.returncode,before_stdout=before.stdout,before_stderr=before.stderr,
            patch_command=['patch',str(candidate)],patch_source=str(diff.relative_to(ROOT)),
            patch_exit=patched.returncode,patch_stdout=patched.stdout,after_exit=after.returncode,
            after_stdout=after.stdout,after_stderr=after.stderr,candidate_cleanup='TEMPORARY_DIRECTORY_REMOVED'))
        print(f'challenge={case} before_exit={before.returncode} patch_exit={patched.returncode} after_exit={after.returncode}')
output=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning/challenge-receipts.json'
output.write_text(json.dumps(dict(verdict='PASS',receipts=receipts),ensure_ascii=False,indent=2)+'\n')
