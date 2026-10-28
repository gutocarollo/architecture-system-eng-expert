"""Verify the learner's old copy fails and the same patched copy passes."""
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
with tempfile.TemporaryDirectory(prefix='airflow-retry-') as directory:
    folder=Path(directory);candidate=folder/'candidate.py';candidate.write_text((HERE/'before.py').read_text())
    command=['python3',str(HERE/'run.py'),'--candidate',str(candidate),'--out',str(folder/'receipt.json')]
    before=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    patch=subprocess.run(['patch','-p0','-d',str(folder)],input=(HERE/'source.patch').read_text(),text=True,capture_output=True)
    after=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    if before.returncode!=1 or 'transient_lock: after violates retry contract' not in before.stderr:
        raise AssertionError('The old candidate did not fail on the intended retry invariant')
    if patch.returncode!=0 or after.returncode!=0:
        raise AssertionError(patch.stderr+after.stderr)
    receipt=dict(observed_at=datetime.now(timezone.utc).isoformat(),before_exit=before.returncode,
                 before_error=before.stderr,patch_exit=patch.returncode,after_exit=after.returncode,
                 after_output=after.stdout,verdict='PASS')
(ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/airflow-learning/challenge.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Airflow editable challenge: old candidate exit1, patch exit0, fixed candidate exit0.')
