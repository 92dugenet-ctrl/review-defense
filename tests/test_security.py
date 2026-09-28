from __future__ import annotations

from datetime import timedelta

import pytest

from src.identity import normalize_email
from src.security_hardening import RateLimiter, Session, hash_password, require_tenant, utc_now, validate_upload, verify_password


def test_passwords_are_hashed_and_verified():
    encoded = hash_password("CorrectHorseBatteryStaple!42")
    assert encoded != "CorrectHorseBatteryStaple!42"
    assert verify_password("CorrectHorseBatteryStaple!42", encoded)
    assert not verify_password("wrong-password", encoded)


def test_password_policy_rejects_short_passwords():
    with pytest.raises(ValueError):
        hash_password("short")


def test_tenant_boundary_and_session_expiry_are_enforced():
    session = Session("user-1", "org-1", "OWNER", "token-hash", utc_now() + timedelta(minutes=5))
    require_tenant(session, "org-1")
    with pytest.raises(PermissionError):
        require_tenant(session, "org-2")


def test_rate_limiter_is_bounded():
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("client", now=1000)
    assert limiter.allow("client", now=1001)
    assert not limiter.allow("client", now=1002)


def test_upload_validation_rejects_unsafe_or_unknown_files():
    validate_upload(size_bytes=10, content_type="application/pdf", filename="evidence.pdf")
    with pytest.raises(ValueError):
        validate_upload(size_bytes=10, content_type="application/octet-stream", filename="evidence.bin")
    with pytest.raises(ValueError):
        validate_upload(size_bytes=10, content_type="application/pdf", filename="../evidence.pdf")


def test_email_normalization_is_strict():
    assert normalize_email("  USER@Example.COM ") == "user@example.com"
    with pytest.raises(ValueError):
        normalize_email("not-an-email")
