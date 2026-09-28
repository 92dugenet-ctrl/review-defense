from datetime import timedelta

import pytest

from src.security_hardening import (
    Session, RateLimiter, can_manage_security, content_sha256,
    generate_session_token, hash_password, hash_token, require_tenant,
    sanitize_external_reference, utc_now, validate_upload, verify_password,
)


def test_password_hash_is_salted_and_verifiable():
    a = hash_password("correct horse battery staple")
    b = hash_password("correct horse battery staple")
    assert a != b
    assert verify_password("correct horse battery staple", a)
    assert not verify_password("wrong password", a)


def test_short_password_rejected():
    with pytest.raises(ValueError):
        hash_password("short")


def test_opaque_session_token_is_hashed():
    raw, digest = generate_session_token()
    assert raw
    assert digest == hash_token(raw)
    assert raw not in digest


def test_session_expiration_and_revocation():
    raw, digest = generate_session_token()
    now = utc_now()
    session = Session("u1", "org1", "ANALYST", digest, now + timedelta(minutes=5))
    assert session.matches(raw, now=now)
    assert not session.matches(raw, now=now + timedelta(minutes=6))
    revoked = Session("u1", "org1", "ANALYST", digest, now + timedelta(minutes=5), now)
    assert not revoked.active(now=now)


def test_tenant_isolation():
    raw, digest = generate_session_token()
    session = Session("u1", "org1", "ANALYST", digest, utc_now() + timedelta(minutes=5))
    require_tenant(session, "org1")
    with pytest.raises(PermissionError):
        require_tenant(session, "org2")


def test_rate_limit():
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("ip:1", now=100)
    assert limiter.allow("ip:1", now=101)
    assert not limiter.allow("ip:1", now=102)
    assert limiter.allow("ip:1", now=161)


def test_upload_validation():
    validate_upload(size_bytes=100, content_type="application/pdf", filename="receipt.pdf")
    with pytest.raises(ValueError):
        validate_upload(size_bytes=100, content_type="application/x-executable", filename="x")
    with pytest.raises(ValueError):
        validate_upload(size_bytes=100, content_type="application/pdf", filename="../x.pdf")


def test_content_hash():
    assert content_sha256(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_external_reference_validation():
    assert sanitize_external_reference("google:review:123") == "google:review:123"
    with pytest.raises(ValueError):
        sanitize_external_reference("bad\nref")


def test_security_roles():
    assert can_manage_security("OWNER")
    assert can_manage_security("ADMIN")
    assert not can_manage_security("ANALYST")
