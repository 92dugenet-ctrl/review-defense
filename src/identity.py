"""V6.2 authentication and organization identity primitives."""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable
from .security_hardening import generate_session_token, hash_password, hash_token, verify_password, utc_now, Session

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ROLES = {"OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER"}
EDIT_ROLES = {"OWNER", "ADMIN", "ANALYST"}
ORG_MANAGERS = {"OWNER", "ADMIN"}

@dataclass(frozen=True)
class Invitation:
    invitation_id: str
    organization_id: str
    email: str
    role: str
    token_hash: str
    expires_at: object
    invited_by: str
    accepted_at: object | None = None
    revoked_at: object | None = None


def normalize_email(email: str) -> str:
    value = (email or "").strip().lower()
    if not EMAIL_RE.match(value) or len(value) > 320:
        raise ValueError("invalid email")
    return value


def validate_role(role: str) -> str:
    if role not in ROLES:
        raise ValueError("invalid role")
    return role


def validate_password(password: str) -> None:
    # Keep the existing PBKDF2 primitive as the single password policy boundary.
    hash_password(password)


def issue_session(*, user_id: str, organization_id: str, role: str, ttl_seconds: int = 3600):
    validate_role(role)
    if ttl_seconds <= 0 or ttl_seconds > 7 * 24 * 3600:
        raise ValueError("invalid session ttl")
    raw, hashed = generate_session_token()
    session = Session(user_id, organization_id, role, hashed,
                      utc_now() + timedelta(seconds=ttl_seconds))
    return raw, session


def authenticate(password: str, password_hash: str) -> bool:
    return isinstance(password, str) and verify_password(password, password_hash)


def can_manage_org(role: str) -> bool:
    return role in ORG_MANAGERS


def can_manage_members(role: str) -> bool:
    return role in ORG_MANAGERS


def can_change_own_password(role: str) -> bool:
    return role in ROLES
