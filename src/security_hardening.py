"""Primitives de sécurité transverses appelées par l'API.

Le module fournit le hachage des mots de passe et tokens, le modèle de session,
le rate limiting et la validation des fichiers. src.api_server orchestre ces
fonctions dans les contrôles HTTP ; ce module ne définit pas de routes.
"""

# Socle partagé de sécurité : hachage, sessions opaques, contrôle du tenant, limitation de débit et validation d'upload. Ces fonctions sont des primitives ; l'API les compose dans le parcours HTTP et doit toujours vérifier les autorisations métier.

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import threading
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
    if len(password) > 256:
        raise ValueError("password must not exceed 256 characters")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    if not isinstance(password, str) or len(password) > 256:
        return False
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
    if not isinstance(token, str) or not token:
        raise ValueError("token is required")
    if len(token) > 4096:
        raise ValueError("token is too long")
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True)
class Session:
    """Session opaque liée à un utilisateur, une organisation et un rôle.

    Seul le hash du token est conservé côté serveur ; le token brut est remis
    au client lors de l'authentification.
    """

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
    """Limiteur mémoire à fenêtre fixe, partagé entre threads du processus.

    Cette instance locale ne constitue pas un compteur distribué entre workers.
    """
    def __init__(self, *, limit: int, window_seconds: int = 60, max_keys: int = 10000):
        if limit <= 0 or window_seconds <= 0 or max_keys <= 0:
            raise ValueError("limit, window_seconds and max_keys must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.RLock()

    def allow(self, key: str, *, now: float | None = None) -> bool:
        if not key or len(key) > 1024:
            raise ValueError("rate-limit key is invalid")
        now = time.time() if now is None else now
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if now - t < self.window_seconds]
            if len(hits) >= self.limit:
                self._hits[key] = hits
                return False
            if key not in self._hits and len(self._hits) >= self.max_keys:
                oldest = min(self._hits, key=lambda k: self._hits[k][-1] if self._hits[k] else now)
                self._hits.pop(oldest, None)
            hits.append(now)
            self._hits[key] = hits
            return True


def validate_upload(
    *,
    size_bytes: int,
    content_type: str,
    filename: str,
    content: bytes | None = None,
) -> None:
    """Validate upload metadata and, when available, the actual byte signature."""
    if size_bytes < 0 or size_bytes > MAX_UPLOAD_BYTES:
        raise ValueError("upload exceeds configured size limit")
    normalized_type = content_type.split(";", 1)[0].strip().lower()
    if normalized_type not in ALLOWED_UPLOAD_TYPES:
        raise ValueError("unsupported content type")
    name = Path(filename).name
    if (
        not name
        or name != filename
        or ".." in name
        or len(name) > 255
        or any(ord(char) < 32 or ord(char) == 127 for char in name)
    ):
        raise ValueError("unsafe filename")
    if content is None:
        return
    if len(content) != size_bytes:
        raise ValueError("upload size does not match its content")
    signatures = {
        "application/pdf": content.startswith(b"%PDF-"),
        "image/jpeg": content.startswith(bytes((0xFF, 0xD8, 0xFF))),
        "image/png": content.startswith(bytes((0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A))),
        "image/webp": (
            len(content) >= 12
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
        ),
    }
    if normalized_type in signatures:
        if not signatures[normalized_type]:
            raise ValueError("file signature does not match declared content type")
        return
    if normalized_type in {"text/plain", "text/csv"}:
        try:
            decoded = content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ValueError("text uploads must use valid UTF-8") from exc
        if "\x00" in decoded or any(
            ord(char) < 32 and char not in "\t\n\r\f"
            for char in decoded
        ):
            raise ValueError("text upload contains binary control characters")
        return
    raise ValueError("unsupported content type")


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
