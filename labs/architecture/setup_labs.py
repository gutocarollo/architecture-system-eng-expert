"""Install only the pinned local SDK environment required by the observability lab."""
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if sys.version_info<(3,11):raise SystemExit('Python 3.11 or newer is required.')
if not shutil.which('openssl'):raise SystemExit('OpenSSL 3.x CLI is required for the local mTLS handshake exercise.')
openssl_version=subprocess.check_output(['openssl','version'],text=True).strip()
if not openssl_version.startswith('OpenSSL 3.'):
    raise SystemExit('Use an OpenSSL 3.x CLI on PATH; the measured version is OpenSSL 3.6.5.')
python=ROOT/'.venv/bin/python'
if not python.exists():venv.EnvBuilder(with_pip=True).create(ROOT/'.venv')
subprocess.run([str(python),'-m','pip','install','--no-cache-dir','-r',str(ROOT/'requirements-lock.txt')],check=True)
print('setup=PASS environment=labs/architecture/.venv network_exporters=disabled')
