"""Prove both editable SQL challenges fail before, and pass after, the patch."""
import difflib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
cache = ROOT / '.pg-learning'
cache.mkdir(exist_ok=True)
receipts = []
for case in ['grain', 'revision']:
    with tempfile.TemporaryDirectory(prefix='challenge-', dir=cache) as directory:
        folder = Path(directory)
        candidate = folder / 'candidate.sql'
        before = (HERE / f'{case}-before.sql.template').read_text()
        after = (HERE / f'{case}-after.sql.template').read_text()
        candidate.write_text(before)
        patch = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                            fromfile='candidate.sql', tofile='candidate.sql'))
        (HERE / f'{case}.patch').write_text(patch)
        command = ['python3', str(HERE / 'run.py'), '--case', case, '--candidate-' + case, str(candidate)]
        first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        applied = subprocess.run(['patch', '-p0', '-d', str(folder)], input=patch, text=True, capture_output=True)
        fixed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert first.returncode != 0, f'{case}: the old query escaped the result invariant'
        assert applied.returncode == 0, applied.stderr
        assert fixed.returncode == 0, fixed.stderr
        receipts.append(dict(case=case, observed_at=datetime.now(timezone.utc).isoformat(),
                             before_exit=first.returncode, before_error=first.stderr,
                             patch_exit=applied.returncode, after_exit=fixed.returncode, after_output=fixed.stdout))
output = ROOT / 'tasks/FBI-4991-arquitetura-nextra/execution/postgres-learning/challenges.json'
output.write_text(json.dumps(dict(verdict='PASS', receipts=receipts), indent=2) + '\n')
print('PostgreSQL editable challenges: two before failures, two applied patches, two after passes.')
