from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dr_validate", ROOT / "scripts/dr_validate.py")
dr = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
a = SPEC.loader
a.exec_module(dr)


def test_source_requires_explicit_test_database(monkeypatch, capsys):
    monkeypatch.delenv("REVIEW_DEFENSE_TEST_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://prod.example/production")
    monkeypatch.setattr("sys.argv", ["dr_validate.py"])
    assert dr.main() == 2
    assert "REVIEW_DEFENSE_TEST_DATABASE_URL" in capsys.readouterr().err


def test_restore_requires_confirmation_and_separate_target(monkeypatch, capsys):
    monkeypatch.setenv("REVIEW_DEFENSE_TEST_DATABASE_URL", "postgresql://u:p@test/review_test")
    monkeypatch.setattr("sys.argv", ["dr_validate.py"])
    assert dr.main() == 2
    assert "--restore-database-url" in capsys.readouterr().err

    monkeypatch.setattr(dr, "_safe_dsn", lambda x: "same" if "review_test" in x else x)
    monkeypatch.setattr(dr, "_is_production_dsn", lambda x: False)
    monkeypatch.setattr(os, "environ", {"REVIEW_DEFENSE_TEST_DATABASE_URL": "postgresql://u:p@test/review_test"})


def test_production_target_is_rejected(monkeypatch, capsys):
    monkeypatch.setenv("REVIEW_DEFENSE_TEST_DATABASE_URL", "postgresql://u:p@test/review_test")
    monkeypatch.setattr("sys.argv", ["dr_validate.py", "--restore-database-url", "postgresql://u:p@test/production", "--confirm"])
    assert dr.main() == 2
    assert "production" in capsys.readouterr().err.lower()

def test_backup_hash_is_deterministic(tmp_path):
    payload = b"review-defense-v6.30"
    path = tmp_path / "backup.dump"
    path.write_bytes(payload)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(payload).hexdigest()


def test_validate_restored_state_contract(monkeypatch):
    class Cursor:
        def __init__(self): self.i = 0
        def execute(self, sql, params=None): self.i += 1
        def fetchone(self):
            rows = [
                ("022", "checksum"), (1,), (1,), (1,),
                ("abc",), (1,), (1,), (1,), (0,)
            ]
            return rows[self.i - 1]
    class Ctx:
        def __enter__(self): return self
        def __exit__(self, *a): return False
    class Conn:
        def transaction(self): return Ctx()
        def cursor(self):
            c = Cursor()
            class CursorCtx:
                def __enter__(self): return c
                def __exit__(self, *a): return False
            return CursorCtx()
        def close(self): pass
    monkeypatch.setattr(dr, "_connect", lambda dsn: Conn())
    s = {"org_a":"a","org_b":"b","case_a":"c","evidence_a":"e","evidence_sha256":"abc"}
    result = dr._validate_restored_state("dsn", s)
    assert result["migrations_present"] is True
    assert result["tenant_a_restored"] is True
    assert result["tenant_rls_isolation"] is True
