"""V5.2 Evidence Vault: tenant-scoped object storage boundary.
Framework-neutral reference implementation. No external network calls.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from .security_hardening import validate_upload

MAX_PRESIGNED_SECONDS = 15 * 60


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


@dataclass(frozen=True)
class StoredObject:
    organization_id: str
    evidence_id: str
    object_key: str
    size_bytes: int
    content_type: str
    sha256: str
    created_at: datetime


class ObjectStore(Protocol):
    def put(self, *, organization_id: str, evidence_id: str, content: bytes,
            content_type: str, filename: str) -> StoredObject: ...
    def get(self, *, organization_id: str, object_key: str) -> bytes: ...
    def delete(self, *, organization_id: str, object_key: str) -> None: ...


def build_object_key(organization_id: str, evidence_id: str, filename: str) -> str:
    if not organization_id or not evidence_id:
        raise ValueError("organization and evidence identifiers are required")
    safe_name = Path(filename).name
    if safe_name != filename or not safe_name or ".." in safe_name:
        raise ValueError("unsafe filename")
    # Never use user-controlled filenames as the object identity.
    suffix = Path(safe_name).suffix.lower()[:16]
    return f"evidence/{organization_id}/{evidence_id}/{secrets.token_hex(16)}{suffix}"


class InMemoryObjectStore:
    """Deterministic test/reference object store with tenant isolation."""
    def __init__(self) -> None:
        self._objects: dict[str, tuple[str, bytes]] = {}
        self._meta: dict[str, StoredObject] = {}

    def put(self, *, organization_id: str, evidence_id: str, content: bytes,
            content_type: str, filename: str) -> StoredObject:
        validate_upload(size_bytes=len(content), content_type=content_type, filename=filename)
        key = build_object_key(organization_id, evidence_id, filename)
        obj = StoredObject(organization_id, evidence_id, key, len(content), content_type,
                           hashlib.sha256(content).hexdigest(), utc_now())
        self._objects[key] = (organization_id, bytes(content))
        self._meta[key] = obj
        return obj

    def get(self, *, organization_id: str, object_key: str) -> bytes:
        row = self._objects.get(object_key)
        if row is None:
            raise KeyError("object not found")
        owner, content = row
        if owner != organization_id or not object_key.startswith(f"evidence/{organization_id}/"):
            raise PermissionError("organization boundary violation")
        return content

    def delete(self, *, organization_id: str, object_key: str) -> None:
        if object_key not in self._objects:
            raise KeyError("object not found")
        owner, _ = self._objects[object_key]
        if owner != organization_id:
            raise PermissionError("organization boundary violation")
        del self._objects[object_key]
        self._meta.pop(object_key, None)

    def metadata(self, object_key: str) -> StoredObject:
        try:
            return self._meta[object_key]
        except KeyError:
            raise KeyError("object not found")


class FilesystemObjectStore:
    """Local development adapter; production should use a private object store."""
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, organization_id: str, object_key: str) -> Path:
        if not organization_id or not object_key.startswith(f"evidence/{organization_id}/"):
            raise PermissionError("organization boundary violation")
        candidate = (self.root / object_key).resolve()
        if self.root not in candidate.parents:
            raise PermissionError("unsafe object path")
        return candidate

    def put(self, *, organization_id: str, evidence_id: str, content: bytes,
            content_type: str, filename: str) -> StoredObject:
        validate_upload(size_bytes=len(content), content_type=content_type, filename=filename)
        key = build_object_key(organization_id, evidence_id, filename)
        path = self._path(organization_id, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredObject(organization_id, evidence_id, key, len(content), content_type,
                            hashlib.sha256(content).hexdigest(), utc_now())

    def get(self, *, organization_id: str, object_key: str) -> bytes:
        path = self._path(organization_id, object_key)
        return path.read_bytes()

    def delete(self, *, organization_id: str, object_key: str) -> None:
        self._path(organization_id, object_key).unlink()


def verify_integrity(content: bytes, expected_sha256: str) -> bool:
    return hmac.compare_digest(hashlib.sha256(content).hexdigest(), expected_sha256)


def sign_download_url(*, object_key: str, organization_id: str, secret: bytes,
                      expires_in: int = 300, now: datetime | None = None) -> str:
    if expires_in <= 0 or expires_in > MAX_PRESIGNED_SECONDS:
        raise ValueError("invalid expiry")
    if not object_key.startswith(f"evidence/{organization_id}/"):
        raise PermissionError("organization boundary violation")
    now = now or utc_now()
    exp = int((now + timedelta(seconds=expires_in)).timestamp())
    payload = f"{organization_id}\n{object_key}\n{exp}".encode()
    sig = _b64(hmac.new(secret, payload, hashlib.sha256).digest())
    return f"vault://download?org={_b64(organization_id.encode())}&key={_b64(object_key.encode())}&exp={exp}&sig={sig}"


def verify_download_url(*, object_key: str, organization_id: str, expires_at: int,
                        signature: str, secret: bytes, now: datetime | None = None) -> bool:
    now = now or utc_now()
    if expires_at < int(now.timestamp()):
        return False
    if not object_key.startswith(f"evidence/{organization_id}/"):
        return False
    payload = f"{organization_id}\n{object_key}\n{expires_at}".encode()
    expected = _b64(hmac.new(secret, payload, hashlib.sha256).digest())
    return hmac.compare_digest(expected, signature)
