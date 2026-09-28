"""V5.9 PostgreSQL production sync boundary.
All event claiming, review upsert and job enqueue operations are tenant-scoped
and transactionally safe. This module is adapter-only: it never calls Google.
"""
from __future__ import annotations
import hashlib, json, time, uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Mapping
from .background_jobs import Job, JobState, JobIdempotencyConflict, JobNotFound

class PostgresSyncError(RuntimeError): pass

@dataclass(frozen=True)
class PubSubReceipt:
    event_id: str
    accepted: bool
    job_id: str | None

class PostgresSyncRepository:
    def __init__(self, dsn: str, connect_factory=None, clock=time.time):
        self.dsn, self._connect_factory, self.clock = dsn, connect_factory, clock
    def _connect(self):
        if self._connect_factory: return self._connect_factory(self.dsn)
        try:
            import psycopg
        except ImportError as exc:
            raise PostgresSyncError("psycopg is required for PostgreSQL sync persistence") from exc
        return psycopg.connect(self.dsn)
    @contextmanager
    def _tx(self, org):
        if not org: raise ValueError("organization_id is required")
        conn=self._connect()
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL app.organization_id = %s", (org,))
                    yield conn,cur
        finally: conn.close()
    def claim_event_and_enqueue(self, organization_id: str, event_id: str, kind: str, payload: Mapping[str,Any], *, priority=0, max_attempts=3):
        fp=self.fingerprint(payload); now=self.clock()
        with self._tx(organization_id) as (_,cur):
            cur.execute("INSERT INTO google_processed_events (organization_id,event_id) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING event_id", (organization_id,event_id))
            if cur.fetchone() is None: return PubSubReceipt(event_id,False,None)
            cur.execute("""INSERT INTO background_jobs (organization_id,kind,payload,state,priority,max_attempts,run_after,idempotency_key,payload_fingerprint)
                         VALUES (%s,%s,%s::jsonb,'QUEUED',%s,%s,now(),%s,%s)
                         ON CONFLICT (organization_id,idempotency_key) DO NOTHING RETURNING id""", (organization_id,kind,json.dumps(payload,sort_keys=True),priority,max_attempts,event_id,fp))
            row=cur.fetchone()
            return PubSubReceipt(event_id,True,str(row[0]) if row else None)
    def upsert_cursor(self, organization_id, account_id, location_id, next_page_token):
        with self._tx(organization_id) as (_,cur):
            cur.execute("""INSERT INTO google_sync_cursors (organization_id,account_id,location_id,next_page_token)
                         VALUES (%s,%s,%s,%s) ON CONFLICT (organization_id,account_id,location_id)
                         DO UPDATE SET next_page_token=excluded.next_page_token,updated_at=now()
                         RETURNING next_page_token""", (organization_id,account_id,location_id,next_page_token))
            return cur.fetchone()[0]
    def get_cursor(self, organization_id, account_id, location_id):
        with self._tx(organization_id) as (_,cur):
            cur.execute("SELECT next_page_token FROM google_sync_cursors WHERE organization_id=%s AND account_id=%s AND location_id=%s", (organization_id,account_id,location_id))
            row=cur.fetchone(); return None if row is None else row[0]
    def upsert_review(self, organization_id, account_id, location_id, review, fingerprint, raw_payload=None):
        with self._tx(organization_id) as (_,cur):
            cur.execute("""INSERT INTO google_reviews (organization_id,review_id,account_id,location_id,rating,review_text,author_display_name,published_at,updated_at,language,review_url,fingerprint,raw_payload)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                         ON CONFLICT (organization_id,review_id) DO UPDATE SET rating=excluded.rating,review_text=excluded.review_text,
                         author_display_name=excluded.author_display_name,published_at=excluded.published_at,updated_at=excluded.updated_at,
                         language=excluded.language,review_url=excluded.review_url,fingerprint=excluded.fingerprint,raw_payload=excluded.raw_payload,observed_at=now()
                         RETURNING review_id""", (organization_id,review.review_id,account_id,location_id,review.rating,review.text,review.author_display_name,review.published_at,review.updated_at,review.language,review.review_url,fingerprint,json.dumps(raw_payload or {},sort_keys=True)))
            return cur.fetchone()[0]
    @staticmethod
    def fingerprint(payload: Mapping[str,Any]):
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

class PostgresJobQueue:
    """PostgreSQL equivalent of the V5.6 queue; API intentionally mirrors enqueue/get/claim/finish primitives."""
    def __init__(self, dsn, connect_factory=None, clock=time.time): self.repo=PostgresSyncRepository(dsn,connect_factory,clock); self.clock=clock
    @staticmethod
    def _job_from_row(r):
        if not r: return None
        return Job(str(r[0]),str(r[1]),r[2],r[3],JobState(r[4]),r[5],r[6],r[7],r[8],r[9],r[10],r[11],r[12],r[13],r[14],r[15])

    def enqueue(self, *, organization_id, kind, payload, priority=0, max_attempts=3, run_after=None, idempotency_key=None):
        fp=self.repo.fingerprint(payload)
        with self.repo._tx(organization_id) as (_,cur):
            if idempotency_key:
                cur.execute("SELECT id,payload_fingerprint FROM background_jobs WHERE organization_id=%s AND idempotency_key=%s",(organization_id,idempotency_key)); old=cur.fetchone()
                if old:
                    if old[1]!=fp: raise JobIdempotencyConflict("idempotency key reused with different payload")
                    cur.execute("SELECT id,organization_id,kind,payload,state,priority,attempts,max_attempts,extract(epoch from run_after),idempotency_key,payload_fingerprint,lease_owner,extract(epoch from leased_until),last_error,extract(epoch from created_at),extract(epoch from updated_at) FROM background_jobs WHERE id=%s",(old[0],))
                    return self._job_from_row(cur.fetchone())
            cur.execute("""INSERT INTO background_jobs (organization_id,kind,payload,state,priority,max_attempts,run_after,idempotency_key,payload_fingerprint)
                         VALUES (%s,%s,%s::jsonb,'QUEUED',%s,%s,COALESCE(to_timestamp(%s),now()),%s,%s) RETURNING id,organization_id,kind,payload,state,priority,attempts,max_attempts,extract(epoch from run_after),idempotency_key,payload_fingerprint,lease_owner,extract(epoch from leased_until),last_error,extract(epoch from created_at),extract(epoch from updated_at)""",(organization_id,kind,json.dumps(payload,sort_keys=True),priority,max_attempts,run_after,idempotency_key,fp))
            return self._job_from_row(cur.fetchone())
    def get(self,job_id,*,organization_id=None):
        with self.repo._tx(organization_id or "") as (_,cur):
            q="SELECT id,organization_id,kind,payload,state,priority,attempts,max_attempts,extract(epoch from run_after),idempotency_key,payload_fingerprint,lease_owner,extract(epoch from leased_until),last_error,extract(epoch from created_at),extract(epoch from updated_at) FROM background_jobs WHERE id=%s"
            cur.execute(q,(job_id,)); r=cur.fetchone()
            if not r: raise JobNotFound(job_id)
            if organization_id and str(r[1])!=organization_id: raise JobNotFound(job_id)
            return self._job_from_row(r)
    def claim(self, *, worker_id, lease_seconds=30):
        if not worker_id or lease_seconds<=0: raise ValueError("worker_id and positive lease_seconds are required")
        raise PostgresSyncError("claim requires an organization-scoped transaction; use claim_for_tenant")
    def claim_for_tenant(self, organization_id, *, worker_id, lease_seconds=30):
        with self.repo._tx(organization_id) as (_,cur):
            cur.execute("""WITH candidate AS (SELECT id FROM background_jobs WHERE organization_id=%s AND state IN ('QUEUED','RETRY_SCHEDULED') AND run_after<=now() ORDER BY priority DESC,created_at ASC FOR UPDATE SKIP LOCKED LIMIT 1)
                         UPDATE background_jobs j SET state='RUNNING',attempts=j.attempts+1,lease_owner=%s,leased_until=now()+make_interval(secs=>%s),updated_at=now() FROM candidate WHERE j.id=candidate.id
                         RETURNING j.id,j.organization_id,j.kind,j.payload,j.state,j.priority,j.attempts,j.max_attempts,extract(epoch from j.run_after),j.idempotency_key,j.payload_fingerprint,j.lease_owner,extract(epoch from j.leased_until),j.last_error,extract(epoch from j.created_at),extract(epoch from j.updated_at)""",(organization_id,worker_id,lease_seconds)); r=cur.fetchone()
            if not r:return None
            return Job(str(r[0]),str(r[1]),r[2],r[3],JobState(r[4]),r[5],r[6],r[7],r[8],r[9],r[10],r[11],r[12],r[13],r[14],r[15])
