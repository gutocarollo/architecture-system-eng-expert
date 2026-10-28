"""Scan decoded publication metadata and verify any typed Git-revision flags."""
import concurrent.futures
import gzip
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent


def verify_revision(pair):
    repo, revision = pair
    result = subprocess.run(
        ['gh', 'api', f'repos/{repo}/commits/{revision}', '--jq', '.sha'],
        capture_output=True, text=True, check=False,
    )
    return dict(repo=repo, revision=revision, exit_code=result.returncode,
                match=result.returncode == 0 and result.stdout.strip() == revision)


def scan():
    files = []
    with tempfile.TemporaryDirectory(prefix='fbi4991-curation-scan-') as temp:
        decoded = {}
        for name in ['matrix.json.gz', 'sources.json.gz']:
            source = BASE / 'curation' / name
            data = gzip.decompress(source.read_bytes())
            json.loads(data)
            decoded[name[:-3]] = data.decode()
            (Path(temp) / name[:-3]).write_bytes(data)
            files.append(dict(path=str(source.relative_to(ROOT)),
                              compressed_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                              decoded_sha256=hashlib.sha256(data).hexdigest(), decoded_bytes=len(data)))
        sources = json.loads(decoded['sources.json'])
        report = BASE / 'curation-decompressed-secrets.json'
        command = ['gitleaks', 'dir', temp, '--max-target-megabytes', '20', '--redact=100',
                   '--report-format', 'json', '--report-path', str(report)]
        first = subprocess.run(command, capture_output=True, text=True, check=False)
        (BASE / 'curation-decompressed-secrets.log').write_text(first.stdout + first.stderr)
        findings = json.loads(report.read_text())
        candidates = []
        unexplained = []
        pairs = set()
        for finding in findings:
            filename = Path(finding['File']).name
            if finding['RuleID'] != 'sourcegraph-access-token' or filename != 'sources.json':
                unexplained.append(dict(file=filename, line=finding['StartLine'], rule=finding['RuleID']))
                continue
            line = decoded[filename].splitlines()[finding['StartLine'] - 1]
            match = re.fullmatch(r'\s*"revision"\s*:\s*"([0-9a-f]{40})",?\s*', line)
            if not match:
                unexplained.append(dict(file=filename, line=finding['StartLine'], rule=finding['RuleID']))
                continue
            revision = match.group(1)
            repos = {item['repo'] for item in sources.values()
                     if isinstance(item, dict) and item.get('revision') == revision
                     and re.fullmatch(r'[\w.-]+/[\w.-]+', item.get('repo', ''))}
            if not repos:
                unexplained.append(dict(file=filename, line=finding['StartLine'], rule=finding['RuleID']))
                continue
            pairs.update((repo, revision) for repo in repos)
            candidates.append(finding)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            verified = list(executor.map(verify_revision, sorted(pairs)))
        all_verified = all(item['match'] for item in verified)
        baseline = BASE / 'curation-decompressed-verified-revisions-baseline.json'
        baseline.write_text(json.dumps(candidates if all_verified else [], indent=2) + '\n')
        second_exit = None
        if not unexplained and all_verified and first.returncode in (0, 1):
            second = subprocess.run(command + ['--baseline-path', str(baseline)],
                                    capture_output=True, text=True, check=False)
            (BASE / 'curation-decompressed-verified.log').write_text(second.stdout + second.stderr)
            second_exit = second.returncode
        receipt = dict(observed_at=datetime.now(timezone.utc).isoformat(), files=files,
                       scope='Decoded curation matrix and source metadata only.',
                       initial_findings=len(findings), typed_git_revisions=verified,
                       unexplained=unexplained, verified_scan_exit=second_exit,
                       no_global_scanner_rules_changed=True,
                       verdict='PASS' if second_exit == 0 else 'FAIL')
        (BASE / 'curation-decompressed-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(dict(verdict=receipt['verdict'], findings=len(findings),
                              verified_git_objects=sum(item['match'] for item in verified),
                              unexplained=len(unexplained))))
        return 0 if receipt['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(scan())
