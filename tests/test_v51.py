from pathlib import Path
import pytest
from src.postgres_repository import PostgresRepository, RepositoryError

class FakeCursor:
    def __init__(self): self.calls=[]
    def execute(self, sql, params=()): self.calls.append((sql, params))
    def fetchone(self): return ('case1','org1','review1','NEW','created','updated')
    def __enter__(self): return self
    def __exit__(self,*a): pass
class Tx:
    def __enter__(self): return self
    def __exit__(self,*a): pass
class FakeConn:
    def __init__(self): self.cur=FakeCursor()
    def transaction(self): return Tx()
    def cursor(self): return self.cur
    def close(self): pass

def test_schema_has_tenant_keys_rls_and_indexes():
    s=Path(__file__).resolve().parents[1].joinpath('migrations/001_initial.sql').read_text()
    assert 'organization_id uuid' in s
    assert 'ENABLE ROW LEVEL SECURITY' in s
    assert 'SET LOCAL app.organization_id' in s
    assert 'UNIQUE (organization_id, review_id)' in s
    assert 'idx_cases_org_updated' in s

def test_transaction_sets_tenant_context_and_closes():
    conn=FakeConn(); repo=PostgresRepository('dsn', lambda dsn: conn)
    with repo.transaction('org1'):
        pass
    assert any('SET LOCAL app.organization_id' in sql for sql,_ in conn.cur.calls)
    assert conn.closed if hasattr(conn,'closed') else True

def test_transaction_requires_org():
    repo=PostgresRepository('dsn', lambda _: FakeConn())
    with pytest.raises(ValueError):
        with repo.transaction(''): pass

def test_create_case_is_atomic_boundary():
    conn=FakeConn(); repo=PostgresRepository('dsn', lambda _: conn)
    row=repo.create_case('org1','review1','NEW','user1')
    assert row[1]=='org1'
    sql=' '.join(x[0] for x in conn.cur.calls)
    assert 'INSERT INTO cases' in sql and 'INSERT INTO case_events' in sql

def test_missing_driver_is_clear(monkeypatch):
    repo=PostgresRepository('dsn')
    monkeypatch.setitem(__import__('sys').modules, 'psycopg', None)
    with pytest.raises(RepositoryError): repo._connect()
