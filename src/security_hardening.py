"""V5.0 security-hardening primitives for Review Defense.
Framework-neutral reference layer: no external network or Google calls.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PBKDF2_ITERATIONS = 310_000
TOKEN_BYTES = 32
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_UPLOAD_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/webp",
    "text/plain", "text/csv",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str, *, salt: bytes | None = None,
                  iterations: int = PBKDF2_ITERATIONS) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        ).hex()
        return hmac.compare_digest(candidate, digest_hex)
    except (ValueError, TypeError):
        return False


def generate_session_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(TOKEN_BYTES)
    return raw, hash_token(raw)


def hash_token(token: str) -> str:
    if not token:
        raise ValueError("token is required")
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True)
class Session:
    user_id: str
    organization_id: str
    role: str
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None

    def active(self, *, now: datetime | None = None) -> bool:
        now = now or utc_now()
        return self.revoked_at is None and now < self.expires_at

    def matches(self, raw_token: str, *, now: datetime | None = None) -> bool:
        return self.active(now=now) and hmac.compare_digest(self.token_hash, hash_token(raw_token))


def require_tenant(session: Session, organization_id: str) -> None:
    if not session.active():
        raise PermissionError("session inactive")
    if not organization_id or session.organization_id != organization_id:
        raise PermissionError("organization boundary violation")


class RateLimiter:
    """Small deterministic in-memory fixed-window limiter for the reference layer."""
    def __init__(self, *, limit: int, window_seconds: int = 60):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str, *, now: float | None = None) -> bool:
        if not key:
            raise ValueError("rate-limit key is required")
        now = time.time() if now is None else now
        hits = [t for t in self._hits.get(key, []) if now - t < self.window_seconds]
        if len(hits) >= self.limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True


def validate_upload(*, size_bytes: int, content_type: str, filename: str) -> None:
    if size_bytes < 0 or size_bytes > MAX_UPLOAD_BYTES:
        raise ValueError("upload exceeds configured size limit")
    if content_type not in ALLOWED_UPLOAD_TYPES:
        raise ValueError("unsupported content type")
    name = Path(filename).name
    if not name or name != filename or ".." in name:
        raise ValueError("unsafe filename")


def content_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sanitize_external_reference(value: str) -> str:
    if not value or len(value) > 2048:
        raise ValueError("invalid external reference")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError("control characters are not allowed")
    return value


def can_manage_security(role: str) -> bool:
    return role in {"OWNER", "ADMIN"}


def can_manage_sessions(role: str) -> bool:
    return role in {"OWNER", "ADMIN"}
