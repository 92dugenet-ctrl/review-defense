import pytest
from src.processing_jobs import ProcessingIdempotencyConflict,ProcessingStatus,ProcessingWorker,SQLiteProcessingQueue
def test_pending_trace():
 q=SQLiteProcessingQueue(); j=q.enqueue(organization_id="o1",kind="sync",payload={},request_id="r",correlation_id="c",idempotency_key="k"); assert j.status is ProcessingStatus.PENDING
 e=q.events(j.job_id,organization_id="o1")[0]; assert e.to_status is ProcessingStatus.PENDING and e.request_id=="r" and e.correlation_id=="c"
def test_idempotence():
 q=SQLiteProcessingQueue(); a=q.enqueue(organization_id="o1",kind="x",payload={"a":1},idempotency_key="k"); assert q.enqueue(organization_id="o1",kind="x",payload={"a":1},idempotency_key="k").job_id==a.job_id
 with pytest.raises(ProcessingIdempotencyConflict): q.enqueue(organization_id="o1",kind="x",payload={"a":2},idempotency_key="k")
def test_completed():
 q=SQLiteProcessingQueue(); j=q.enqueue(organization_id="o1",kind="x",payload={}); assert ProcessingWorker(q,{"x":lambda _:None},worker_id="w").run_once().status is ProcessingStatus.COMPLETED
 assert [e.to_status for e in q.events(j.job_id)]==[ProcessingStatus.PENDING,ProcessingStatus.PROCESSING,ProcessingStatus.COMPLETED]
def test_retry_failed():
 q=SQLiteProcessingQueue(); j=q.enqueue(organization_id="o1",kind="x",payload={},max_attempts=2)
 def boom(_): raise ValueError("boom")
 w=ProcessingWorker(q,{"x":boom},worker_id="w",retry_delay=0); assert w.run_once().status is ProcessingStatus.PENDING; assert w.run_once().status is ProcessingStatus.FAILED; assert q.get(j.job_id).attempt==2
def test_lease_and_owner():
 now=[100]; q=SQLiteProcessingQueue(clock=lambda:now[0]); j=q.enqueue(organization_id="o1",kind="x",payload={}); q.claim(worker_id="a",lease_seconds=5); now[0]=106; assert q.recover_expired_leases()==1 and q.get(j.job_id).status is ProcessingStatus.PENDING
 q.claim(worker_id="a")
 with pytest.raises(RuntimeError): q.complete(j.job_id,worker_id="b")
def test_tenant_scope():
 q=SQLiteProcessingQueue(); j=q.enqueue(organization_id="o1",kind="x",payload={})
 with pytest.raises(KeyError): q.get(j.job_id,organization_id="o2")
