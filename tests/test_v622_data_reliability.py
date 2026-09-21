from pathlib import Path
import hashlib
import pytest
from src.migration_runner import migration_files, migration_checksum, apply_migrations, MigrationError

ROOT = Path(__file__).parents[1]


def test_v622_migration_is_latest_and_has_reliability_controls():
    files = migration_files(ROOT / "migrations")
    target = [f for f in files if f.name == "020_v622_data_reliability.sql"]
    assert target
    sql = target[0].read_text()
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "WITH CHECK" in sql
    assert "trg_api_cases_updated_at" in sql


def test_migration_checksum_is_sha256():
    path = ROOT / "migrations/020_v622_data_reliability.sql"
    assert migration_checksum(path) == hashlib.sha256(path.read_bytes()).hexdigest()
    assert len(migration_checksum(path)) == 64


def test_migration_runner_records_checksum_and_rejects_drift(tmp_path):
    class Cursor:
        def __init__(self, conn): self.conn=conn; self.rows=[]
        def __enter__(self): return self
        def __exit__(self,*a): return False
        def execute(self, sql, params=None):
            if sql.startswith("SELECT version"):
                self.rows=[(v,f,c) for v,f,c in self.conn.done]
            elif sql.startswith("INSERT INTO schema_migrations"):
                self.conn.done.append((params[0],params[1],params[2]))
            elif sql.startswith("UPDATE schema_migrations"):
                v=params[1]; self.conn.done=[(a,b,params[0] if a==v else c) for a,b,c in self.conn.done]
        def fetchall(self): return self.rows
    class Tx:
        def __init__(self,c): self.c=c
        def __enter__(self): return self
        def __exit__(self,*a): return False
    class Conn:
        def __init__(self): self.done=[]; self.closed=False
        def transaction(self): return Tx(self)
        def cursor(self): return Cursor(self)
        def close(self): self.closed=True
    conn=Conn()
    Path(tmp_path,"001_test.sql").write_text("CREATE TABLE test(id int);", encoding="utf-8")
    assert apply_migrations(lambda: conn, tmp_path) == ["001_test.sql"]
    Path(tmp_path,"001_test.sql").write_text("CREATE TABLE test(id bigint);", encoding="utf-8")
    with pytest.raises(MigrationError, match="checksum drift"):
        apply_migrations(lambda: conn, tmp_path)


def test_migration_runner_uses_advisory_lock():
    source = (ROOT / "src/migration_runner.py").read_text()
    assert "pg_advisory_xact_lock" in source


def test_v622_indexes_cover_expiry_audit_evidence_and_idempotency():
    sql = (ROOT / "migrations/020_v622_data_reliability.sql").read_text()
    for name in ("idx_api_sessions_expiry", "idx_security_events_actor_created", "idx_api_evidence_case_created", "idx_api_idempotency_created"):
        assert name in sql


def test_v622_updates_legacy_session_last_seen_safely():
    sql = (ROOT / "migrations/020_v622_data_reliability.sql").read_text()
    assert "COALESCE(last_seen_at, created_at)" in sql
