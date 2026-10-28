"""Independently verify and run the exact downloadable source archive."""
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

root = Path.cwd()
output = root / 'tasks/FBI-4991-arquitetura-nextra/execution/reviews'
archive = root / 'public/downloads/architecture-labs.zip'
sha = lambda data: hashlib.sha256(data).hexdigest()
report = {'started_at_utc': datetime.now(timezone.utc).isoformat(), 'archive_sha256': sha(archive.read_bytes()),
          'scope': 'Exact downloadable ZIP extracted without Git, dependencies installed from its locks, sixteen local synthetic runners.', 'commands': []}
with tempfile.TemporaryDirectory(prefix='terminal-fbi4991-download-') as directory:
    destination = Path(directory)
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        assert len(names) == len(set(names))
        for item in package.infolist():
            parts = PurePosixPath(item.filename)
            assert not parts.is_absolute() and '..' not in parts.parts
            assert '.git' not in parts.parts and 'node_modules' not in parts.parts and '.venv' not in parts.parts
            assert (item.external_attr >> 16) & 0o170000 != 0o120000
        package.extractall(destination)
    snapshot = destination / 'architecture-labs'
    manifest = json.loads((snapshot / 'source-manifest.json').read_text())
    assert len(manifest) == 98
    for relative, expected in manifest.items():
        assert sha((snapshot / relative).read_bytes()) == expected, relative
        assert sha((root / relative).read_bytes()) == expected, relative
    report.update(files_verified=len(manifest), members=len(names), manifest_sha256=sha((snapshot / 'source-manifest.json').read_bytes()),
                  extracted_without_git=not (snapshot / '.git').exists(), source_matches_current_checkout=True)
    assert report['extracted_without_git']
    for label, command in [
        ('node-setup', ['npm', 'ci', '--prefix', 'labs/architecture']),
        ('sdk-setup', ['python3', 'labs/architecture/setup_labs.py']),
        ('run', ['python3', 'labs/architecture/run_all.py', '--out', str(output / 'terminal-download-runs.json')])
    ]:
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(command, cwd=snapshot, capture_output=True, text=True, timeout=240)
        log = output / ('terminal-download-' + label + '.log')
        log.write_text(result.stdout + result.stderr)
        report['commands'].append({'command': command, 'cwd': str(snapshot), 'started_at_utc': started,
                                   'exit_code': result.returncode, 'log': str(log), 'log_sha256': sha(log.read_bytes())})
        assert result.returncode == 0, (label, result.returncode)
    run = json.loads((output / 'terminal-download-runs.json').read_text())
    assert run['base_sha'] is None and run['source_revision_kind'] == 'UNVERSIONED_SOURCE_SNAPSHOT'
    assert run['verdict'] == 'PASS' and len(run['receipts']) == 16
    report.update(verdict='PASS', base_sha=run['base_sha'], source_revision_kind=run['source_revision_kind'],
                  runners=len(run['receipts']), all_runner_exit_codes=[r['exit_code'] for r in run['receipts']],
                  production_execution=run['production_execution'])
report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
(output / 'terminal-download.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'commands'}))
