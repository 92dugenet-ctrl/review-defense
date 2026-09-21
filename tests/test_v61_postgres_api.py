from pathlib import Path
from src.postgres_api_repository import PostgresAPIRepository

class C:
    def __init__(self): self.calls=[]
    def execute(self,sql,params=()): self.calls.append((sql,params))
    def fetchone(self):
        sql=self.calls[-1][0]
        if 'INSERT INTO users' in sql: return ('id','user@example.com','hash')
        if 'SELECT u.id' in sql: return ('id','user@example.com','hash','OWNER')
        return ('case','org','r1','NEW',None,None,'now','now')
    def fetchall(self): return []
    def __enter__(self): return self
    def __exit__(self,*a): pass
class T:
    def __enter__(self): return self
    def __exit__(self,*a): pass
class Conn:
    def __init__(self): self.c=C()
    def transaction(self): return T()
    def cursor(self): return self.c
    def close(self): pass

def repo():
    c=Conn(); return PostgresAPIRepository('dsn',lambda _:c),c

def test_migration_covers_api_state_and_rls():
    s=Path('migrations/003_v61_api_persistence.sql').read_text()
    for t in ['api_sessions','api_reviews','api_cases','api_decisions','api_dossier_snapshots','api_approvals','api_submissions','api_idempotency','api_evidence']:
        assert t in s
    assert 'ENABLE ROW LEVEL SECURITY' in s and 'current_setting' in s

def test_all_transactions_set_tenant_context():
    r,c=repo(); r.get_user_by_email('org','user@example.com')
    assert "set_config('app.organization_id', %s, true)" in c.c.calls[0][0]

def test_user_and_membership_are_created_atomically():
    r,c=repo(); r.create_user('org','user@example.com','hash','OWNER')
    sql=' '.join(x[0] for x in c.c.calls)
    assert 'INSERT INTO users' in sql and 'INSERT INTO memberships' in sql

def test_case_creation_and_audit_share_repository_boundary():
    r,c=repo(); r.create_case_persistent('org','case','review','NEW','user')
    sql=' '.join(x[0] for x in c.c.calls)
    assert 'INSERT INTO api_cases' in sql and 'INSERT INTO case_events' in sql

def test_idempotency_is_tenant_scoped():
    r,c=repo(); r.put_idempotency('org','k','fp',{'ok':True})
    assert any('api_idempotency' in x[0] and 'organization_id' in x[0] for x in c.c.calls)


def test_v65_migration_has_rls_and_structured_findings():
    s=Path('migrations/005_v65_contradiction_facts.sql').read_text()
    for t in ['evidence_facts','contradiction_findings']:
        assert t in s
    assert 'ENABLE ROW LEVEL SECURITY' in s and 'current_setting' in s


def test_v65_repository_persists_facts_and_contradictions():
    r,c=repo()
    r.put_evidence_fact('org', {'fact_id':'f','evidence_id':'e','case_id':'case','key':'amount:eur','kind':'AMOUNT','value':'60','source_location':'line 1','verified':True})
    r.put_contradiction('org', {'contradiction_id':'ctr1','case_id':'case','claim_id':'c1','key':'amount:eur','kind':'AMOUNT','claim_value':'50','evidence_ids':['e'],'evidence_values':['60'],'description':'conflict','confidence':0.99,'requires_human_review':True})
    sql=' '.join(x[0] for x in c.c.calls)
    assert 'evidence_facts' in sql and 'contradiction_findings' in sql
