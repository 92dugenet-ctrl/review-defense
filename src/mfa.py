"""V6.24 MFA and account-recovery primitives. Standard-library TOTP (RFC 6238)."""
from __future__ import annotations
import base64, hashlib, hmac, os, secrets, struct, time
from cryptography.fernet import Fernet, InvalidToken

_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")

def _secret_bytes(secret: str) -> bytes:
    return base64.b32decode(secret.upper() + "=" * ((8-len(secret)%8)%8), casefold=True)

def totp_code(secret: str, for_time: int | None = None, step: int = 30, digits: int = 6) -> str:
    counter = int((time.time() if for_time is None else for_time) // step)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(_secret_bytes(secret), msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0f
    value = (struct.unpack(">I", digest[offset:offset+4])[0] & 0x7fffffff) % (10 ** digits)
    return f"{value:0{digits}d}"

def verify_totp(secret: str, code: str, *, now: int | None = None, window: int = 1) -> bool:
    if not isinstance(code, str) or not code.isdigit() or len(code) != 6:
        return False
    base = int(time.time() if now is None else now)
    return any(hmac.compare_digest(totp_code(secret, base + delta*30), code) for delta in range(-window, window+1))

def otpauth_uri(secret: str, email: str, issuer: str = "Review Defense") -> str:
    from urllib.parse import quote
    return f"otpauth://totp/{quote(issuer)}:{quote(email)}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"

def encrypt_secret(secret: str, key: str) -> str:
    return Fernet(key.encode() if isinstance(key, str) else key).encrypt(secret.encode()).decode()

def decrypt_secret(value: str, key: str) -> str:
    try:
        return Fernet(key.encode() if isinstance(key, str) else key).decrypt(value.encode()).decode()
    except (InvalidToken, ValueError, TypeError) as exc:
        raise ValueError("invalid MFA secret") from exc

def recovery_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()
