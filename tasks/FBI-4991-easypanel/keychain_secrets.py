"""Read the course deployment credentials from the owner's macOS Keychain."""
import ctypes
import importlib.util
import json
import sys
import termios
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = root / 'tasks/FBI-4991-arquitetura-nextra/execution/hosting/keychain_secrets.py'
spec = importlib.util.spec_from_file_location('_course_keychain_base', source)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.SERVICE = b'com.fazcapital.easypanel.fbi4991'
base.ACCOUNTS = {'COURSE_PASSWORD': b'course-password', 'COURSE_SESSION_SECRET': b'session-signing-key'}

if '--process-import' in sys.argv:
    old = termios.tcgetattr(sys.stdin.fileno())
    hidden = old.copy()
    hidden[3] &= ~termios.ECHO
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, hidden)
    try:
        print('Ready for deployment credentials JSON on stdin (input is hidden).', flush=True)
        values = json.loads(sys.stdin.readline())
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, old)
    for key, account in base.ACCOUNTS.items():
        value = values[key].encode()
        status = base.SECURITY.SecKeychainAddGenericPassword(None, len(base.SERVICE), base.SERVICE,
            len(account), account, len(value), value, None)
        if status == -25299:
            if base.load_values()[key] != values[key]:
                raise SystemExit('An existing deployment credential differs; it was preserved.')
        elif status != 0:
            raise SystemExit('Keychain write failed with status ' + str(status))
    print(json.dumps({'stored_keys': list(base.ACCOUNTS)}))
elif '--process-export' in sys.argv:
    print(json.dumps(base.load_values()))
else:
    print(json.dumps({'keys': list(base.load_values())}))
