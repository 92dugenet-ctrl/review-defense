from pathlib import Path

import pytest

from scripts.bootstrap_owner import BootstrapError, bootstrap_owner
from scripts.migrate import connect as migration_connect
from src.security_hardening import verify_password

ROOT = Path(__file__).resolve().parents[1]

class FakeResult:
    def __init__(self, row=None): self.row = row
    def fetchone(self): return self.row

class FakeConnection:
    def __init__(self, membership_exists=False):
        self.membership_exists = membership_exists
        self.statements = []
        self.closed = False
    class Transaction:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
    def transaction(self): return self.Transaction()
    def execute(self, sql, params=None):
        text = str(sql)
        self.statements.append((text, params))
        normalized = " ".join(text.split()).lower()
        if "select exists (select 1 from memberships)" in normalized:
            return FakeResult((self.membership_exists,))
        if "insert into organizations" in normalized:
            self.membership_exists = True
            return FakeResult(("org-test",))
        if "insert into users" in normalized:
            return FakeResult(("user-test",))
        return FakeResult()
    def close(self): self.closed = True

def test_v637_bootstrap_requires_explicit_confirmation():
    with pytest.raises(BootstrapError, match="CREATE_OWNER"):
        bootstrap_owner("postgresql://redacted", "Review Defense", "owner@example.com", "a" * 12, confirmation="YES", connect_factory=lambda _: FakeConnection())

def test_v637_bootstrap_rejects_existing_memberships():
    conn = FakeConnection(membership_exists=True)
    with pytest.raises(BootstrapError, match="memberships already exist"):
        bootstrap_owner("postgresql://redacted", "Review Defense", "owner@example.com", "a" * 12, confirmation="CREATE_OWNER", connect_factory=lambda _: conn)
    assert conn.closed is True

def test_v637_bootstrap_creates_owner_and_security_event():
    conn = FakeConnection()
    org_id, user_id = bootstrap_owner("postgresql://redacted", "Review Defense", "OWNER@EXAMPLE.COM", "a" * 12, confirmation="CREATE_OWNER", connect_factory=lambda _: conn)
    assert (org_id, user_id) == ("org-test", "user-test")
    sql_blob = "\n".join(sql for sql, _ in conn.statements)
    assert "INSERT INTO memberships" in sql_blob
    assert "'OWNER'" in sql_blob
    assert "security_events" in sql_blob
    assert "a" * 12 not in sql_blob
    assert conn.closed is True

def test_v637_bootstrap_preserves_password_hashing_policy():
    conn = FakeConnection()
    password = "strong-password-123"
    bootstrap_owner("postgresql://redacted", "Review Defense", "owner@example.com", password, confirmation="CREATE_OWNER", connect_factory=lambda _: conn)
    params = next(params for sql, params in conn.statements if "INSERT INTO users" in sql)
    password_hash = params[1]
    assert password_hash != password
    assert verify_password(password, password_hash)

def test_v637_bootstrap_rejects_short_password():
    with pytest.raises(ValueError, match="at least 12"):
        bootstrap_owner("postgresql://redacted", "Review Defense", "owner@example.com", "short", confirmation="CREATE_OWNER", connect_factory=lambda _: FakeConnection())

def test_v637_bootstrap_rejects_invalid_email():
    with pytest.raises(ValueError, match="invalid email"):
        bootstrap_owner("postgresql://redacted", "Review Defense", "not-an-email", "a" * 12, confirmation="CREATE_OWNER", connect_factory=lambda _: FakeConnection())

def test_v637_migration_launcher_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REVIEW_DEFENSE_DATABASE_URL", raising=False)
    with pytest.raises(SystemExit, match="DATABASE_URL is required"):
        migration_connect()

def test_v637_bootstrap_script_never_prints_password():
    source = (ROOT / "scripts" / "bootstrap_owner.py").read_text(encoding="utf-8")
    assert "BOOTSTRAP_OWNER_PASSWORD" in source
    assert "print(password" not in source
    assert "print(dsn" not in source