from pathlib import Path
import json
import pytest
from src.postgres_sync import PostgresSyncRepository, PostgresJobQueue, JobIdempotencyConflict
from src.google_pubsub_receiver import AuthenticatedPubSubReceiver, PubSubAuthenticationError

class C:
    def __init__(self): self.calls=[]; self.event_claims=0
    def execute(self,sql,params=()): self.calls.append((sql,params))
    def fetchone(self):
        sql=self.calls[-1][0]
        if 'INSERT INTO google_processed_events' in sql:
            self.event_claims += 1
            return ('evt',) if self.event_claims == 1 else None
        if 'INSERT INTO background_jobs' in sql: return ('job-1',)
        if 'SELECT id,payload_fingerprint' in sql: return None
        if 'SELECT next_page_token' in sql: return ('p2',)
        if 'INSERT INTO google_sync_cursors' in sql: return ('p2',)
        return ('review-1',)
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
    c=Conn(); return PostgresSyncRepository('dsn',lambda _:c),c

def test_migration_has_sync_tables_rls_and_atomic_job_index():
    s=Path('migrations/002_v59_google_sync.sql').read_text()
    for x in ['google_sync_cursors','google_processed_events','google_reviews','background_jobs','ENABLE ROW LEVEL SECURITY','FOR UPDATE SKIP LOCKED','UNIQUE (organization_id, idempotency_key)']:
        assert x in s

def test_event_claim_and_job_are_same_transaction():
    r,c=repo(); out=r.claim_event_and_enqueue('org','evt','google.review.event',{'event_id':'evt'})
    assert out.accepted and out.job_id=='job-1'
    assert 'SET LOCAL app.organization_id' in c.c.calls[0][0]
    sql=' '.join(x[0] for x in c.c.calls); assert 'google_processed_events' in sql and 'background_jobs' in sql

def test_cursor_is_tenant_scoped():
    r,c=repo(); assert r.upsert_cursor('org','a','l','p2')=='p2'; assert r.get_cursor('org','a','l')=='p2'

def test_queue_refuses_unscoped_claim():
    q=PostgresJobQueue('dsn',lambda _:Conn())
    with pytest.raises(Exception): q.claim(worker_id='w')

def test_authenticated_receiver_requires_verifier():
    r,c=repo(); recv=AuthenticatedPubSubReceiver(r)
    with pytest.raises(PubSubAuthenticationError): recv.receive('org',{},authorization='x')

def test_authenticated_receiver_deduplicates():
    r,c=repo(); recv=AuthenticatedPubSubReceiver(r,lambda token,env: token=='valid')
    env={'message':{'messageId':'e1','attributes':{'eventType':'NEW_REVIEW','resource':'accounts/a/locations/l/reviews/r1'}}}
    first=recv.receive('org',env,authorization='valid'); second=recv.receive('org',env,authorization='valid')
    assert first.acknowledged and not first.duplicate
    assert second.acknowledged and second.duplicate
