"""Encrypted provider credentials: OS vault at rest, host public key in transit."""
import base64
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _dpapi(data, decrypt=False):
    import ctypes
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_byte))]

    source = ctypes.create_string_buffer(data)
    incoming = Blob(len(data), ctypes.cast(source, ctypes.POINTER(ctypes.c_byte)))
    outgoing = Blob()
    operation = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not operation(ctypes.byref(incoming), None, None, None, None, 1, ctypes.byref(outgoing)):
        raise OSError('The Windows credential vault could not process this key')
    try:
        return ctypes.string_at(outgoing.data, outgoing.size)
    finally:
        ctypes.windll.kernel32.LocalFree(outgoing.data)


def _fernet():
    path = os.environ.get('TACTIC_AGENT_VAULT_KEY_FILE', '')
    if not path:
        raise ValueError('Configure the server vault key file before saving API keys')
    key = Path(path)
    if not key.is_file() or key.stat().st_mode & 0o077:
        raise ValueError('The server vault key file must be private to its account')
    return Fernet(key.read_bytes().strip())


def seal(secret):
    value = secret.encode('utf-8')
    if os.name == 'nt':
        return 'dpapi:' + base64.b64encode(_dpapi(value)).decode('ascii')
    return 'fernet:' + _fernet().encrypt(value).decode('ascii')


def unseal(value):
    try:
        if value.startswith('dpapi:') and os.name == 'nt':
            return _dpapi(base64.b64decode(value[6:], validate=True), decrypt=True).decode('utf-8')
        if value.startswith('fernet:'):
            return _fernet().decrypt(value[7:].encode('ascii')).decode('utf-8')
    except (OSError, ValueError, InvalidToken):
        raise ValueError('The provider key cannot be opened by this server vault; re-enter it in AI providers') from None
    raise ValueError('Provider credential storage does not belong to this vault')


def public_key(value):
    if not isinstance(value, str) or len(value) > 4096:
        raise ValueError('Invalid external host credential key')
    key = serialization.load_pem_public_key(value.encode('ascii'))
    if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
        raise ValueError('External host requires an RSA credential key of at least 2048 bits')
    return key


def host_envelope(secret, host_public_key, scope):
    key, nonce = AESGCM.generate_key(bit_length=256), os.urandom(12)
    encrypted = AESGCM(key).encrypt(nonce, secret.encode('utf-8'), scope.encode('utf-8'))
    wrapped = public_key(host_public_key).encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=scope.encode('utf-8')))
    return {name: base64.b64encode(value).decode('ascii') for name, value in dict(key=wrapped, nonce=nonce, value=encrypted).items()}


def host_secret(envelope, private_key, scope):
    try:
        values = {name: base64.b64decode(envelope[name], validate=True) for name in ('key', 'nonce', 'value')}
        key = private_key.decrypt(values['key'], padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=scope.encode('utf-8')))
        return AESGCM(key).decrypt(values['nonce'], values['value'], scope.encode('utf-8')).decode('utf-8')
    except (KeyError, TypeError, ValueError, InvalidTag):
        raise ValueError('The provider credential package does not belong to this host or was damaged') from None


def new_host_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
    return key, public
