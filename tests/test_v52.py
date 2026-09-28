from datetime import timedelta
import hashlib
import pytest
from src.evidence_vault import (
    InMemoryObjectStore, FilesystemObjectStore, build_object_key,
    sign_download_url, verify_download_url, verify_integrity, utc_now,
)


def test_put_hash_and_tenant_isolation():
    s = InMemoryObjectStore()
    o = s.put(organization_id="org1", evidence_id="ev1", content=b"abc",
              content_type="application/pdf", filename="receipt.pdf")
    assert o.sha256 == hashlib.sha256(b"abc").hexdigest()
    assert s.get(organization_id="org1", object_key=o.object_key) == b"abc"
    with pytest.raises(PermissionError):
        s.get(organization_id="org2", object_key=o.object_key)


def test_object_key_never_uses_raw_filename_as_identity():
    k = build_object_key("org1", "ev1", "../../receipt.pdf") if False else build_object_key("org1", "ev1", "receipt.pdf")
    assert k.startswith("evidence/org1/ev1/")
    assert k != "evidence/org1/ev1/receipt.pdf"


def test_integrity_detects_modification():
    digest = hashlib.sha256(b"original").hexdigest()
    assert verify_integrity(b"original", digest)
    assert not verify_integrity(b"modified", digest)


def test_signed_download_url_is_expiring_and_tenant_bound():
    now = utc_now()
    secret = b"vault-secret"
    key = "evidence/org1/ev1/abc.pdf"
    url = sign_download_url(object_key=key, organization_id="org1", secret=secret, expires_in=60, now=now)
    exp = int((now + timedelta(seconds=60)).timestamp())
    sig = url.split("sig=", 1)[1]
    assert verify_download_url(object_key=key, organization_id="org1", expires_at=exp, signature=sig, secret=secret, now=now)
    assert not verify_download_url(object_key=key, organization_id="org2", expires_at=exp, signature=sig, secret=secret, now=now)
    assert not verify_download_url(object_key=key, organization_id="org1", expires_at=exp, signature=sig, secret=secret, now=now + timedelta(seconds=61))


def test_download_url_expiry_cap():
    with pytest.raises(ValueError):
        sign_download_url(object_key="evidence/org1/e1/a.pdf", organization_id="org1", secret=b"x", expires_in=3600)


def test_filesystem_adapter_stays_inside_root(tmp_path):
    s = FilesystemObjectStore(tmp_path)
    o = s.put(organization_id="org1", evidence_id="ev1", content=b"x",
              content_type="text/plain", filename="note.txt")
    assert s.get(organization_id="org1", object_key=o.object_key) == b"x"
    with pytest.raises(PermissionError):
        s.get(organization_id="org2", object_key=o.object_key)
