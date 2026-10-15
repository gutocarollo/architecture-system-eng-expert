"""Return site secrets to the calling process, keeping their durable copy in Keychain."""
import ctypes
import json
import secrets
import sys

SERVICE = b'com.fazcapital.sites.fbi4991'
ACCOUNTS = {
    'COURSE_PASSWORD': b'course-password',
    'COURSE_SESSION_SECRET': b'session-signing-key',
    'COURSE_UPLOAD_SECRET': b'asset-upload-key',
}
SECURITY = ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
SECURITY.SecKeychainFindGenericPassword.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p,
    ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32),
    ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
SECURITY.SecKeychainFindGenericPassword.restype = ctypes.c_int32
SECURITY.SecKeychainAddGenericPassword.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p,
    ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_void_p]
SECURITY.SecKeychainAddGenericPassword.restype = ctypes.c_int32
SECURITY.SecKeychainItemFreeContent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


def load_values(create=False):
    values = {}
    for key, account in ACCOUNTS.items():
        length, pointer = ctypes.c_uint32(), ctypes.c_void_p()
        status = SECURITY.SecKeychainFindGenericPassword(None, len(SERVICE), SERVICE,
            len(account), account, ctypes.byref(length), ctypes.byref(pointer), None)
        if status == 0:
            try:
                value = ctypes.string_at(pointer, length.value).decode()
            finally:
                SECURITY.SecKeychainItemFreeContent(None, pointer)
        elif status == -25300 and create:
            value = secrets.token_urlsafe(24 if key == 'COURSE_PASSWORD' else 48)
            encoded = value.encode()
            added = SECURITY.SecKeychainAddGenericPassword(None, len(SERVICE), SERVICE,
                len(account), account, len(encoded), encoded, None)
            if added != 0:
                raise RuntimeError(f'Keychain add failed with status {added}')
        else:
            raise RuntimeError(f'Keychain read failed with status {status}')
        values[key] = value
    return values


if __name__ == '__main__':
    if not set(sys.argv[1:]).issubset({'--create', '--process-export'}):
        raise SystemExit('Unsupported option')
    values = load_values(create='--create' in sys.argv)
    if '--process-export' in sys.argv:
        sys.stdout.write(json.dumps(values))
    else:
        print(json.dumps({'stored_in_keychain': True, 'keys': sorted(values)}))
