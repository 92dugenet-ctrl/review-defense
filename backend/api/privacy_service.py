"""Tenant-safe privacy workflow helpers shared by API and future frontend clients."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
import copy


REQUEST_TYPES = {"ACCESS", "RECTIFICATION", "ERASURE", "RESTRICTION", "OBJECTION", "PORTABILITY"}
REQUEST_STATUSES = {"RECEIVED", "IN_REVIEW", "COMPLETED", "REJECTED"}


@dataclass(frozen=True)
class PrivacyRequest:
    request_id: str
    organization_id: str
    requester_user_id: str
    request_type: str
    status: str
    details: Mapping[str, Any]
    due_at: str
    created_at: str
    updated_at: str


def validate_request_type(value: str) -> str:
    value = str(value or "").strip().upper()
    if value not in REQUEST_TYPES:
        raise ValueError("invalid privacy request type")
    return value


def validate_status(value: str) -> str:
    value = str(value or "").strip().upper()
    if value not in REQUEST_STATUSES:
        raise ValueError("invalid privacy request status")
    return value


def new_due_at(*, now: datetime | None = None, days: int = 30) -> str:
    current = now or datetime.now(timezone.utc)
    return (current + timedelta(days=days)).isoformat()


def redact_export(value: Any) -> Any:
    """Remove secrets from a portability/access export without losing structure."""
    secret_keys = {"password_hash", "token", "token_hash", "secret", "secret_enc",
                   "access_token", "recovery_token", "mfa_secret", "api_key"}
    if isinstance(value, Mapping):
        return {str(k): "[REDACTED]" if str(k).lower() in secret_keys else redact_export(v)
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact_export(v) for v in value]
    if isinstance(value, tuple):
        return [redact_export(v) for v in value]
    return copy.deepcopy(value)


def build_export(*, identity: Mapping[str, Any], reviews: list[Any],
                 cases: list[Any], privacy_requests: list[Any],
                 consents: list[Any], audit_events: list[Any]) -> dict[str, Any]:
    return redact_export({
        "schema_version": "2026-09-29",
        "identity": dict(identity),
        "reviews": list(reviews),
        "cases": list(cases),
        "privacy_requests": list(privacy_requests),
        "consents": list(consents),
        "audit_events": list(audit_events),
    })
