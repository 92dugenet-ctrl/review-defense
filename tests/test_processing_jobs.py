import pytest
from src.processing_jobs import ProcessingIdempotencyConflict,ProcessingStatus,ProcessingWorker,SQLiteProcessingQueue

def test_pending_and_trace():
 q=SQLiteProcessingQueue(); j=q.enqueue(organization_id="o1",kind="sync",payload={"x":1},request_id="r",correlation_id="c",idempotency_key="k")
 assert j.status is ProcessingStatus.PENDING
 e=q.events(j.job_id,organization_id="o1"); assert e[0].to_status is ProcessingStatus.PENDING and e[0].request_id=="r" and e[0].correlation_id=="c"

def test_idempotence_and_conflict():
 q=SQLiteProcessingQueue(); a=q.enqueue(organization_id="o1",kind="x",payload={"a":1},idempotency_key="k"); b=q.enqueue(organization_id="o1",kind="x",payload={"a":1},idempotency_key="k"); assert a.job_id==b.job_id
 with pytest.raises(ProcessingIdempotencyConflict): q.enqueue(organization_id="o1",kind="x",payload={"a":2},idempotency_key="k")

def test_completed():
 q=SQLiteProcessingQueue(); j=q.enqueue(organization_id="o1",kind="x",payload={}); out=ProcessingWorker(q,{"x":lambda _:None},worker_id="w").run_once()
 assert out.status is ProcessingStatus.COMPLETED and out.attempt==1
 assert [e.to_status for e in q.events(j.job_id)]==[ProcessingStatus.PENDING,ProcessingStatus.PROCESSING,ProcessingStatus.COMPLETED]

def test_retry_and_terminal_failure():
 q=SQLiteProcessingQueue(); j=q.enqueue(organization_id="o1",kind="x",payload={},max_attempts=2)
 def boom(_): raise ValueError("boom")
 w=ProcessingWorker(q,{"x":boom},worker_id="w",retry_delay=0)
 assert w.run_once().status is ProcessingStatus.PENDING and w.run_once().status is ProcessingStatus.FAILED
 assert q.get(j.job_id).attempt==2 and "ValueError: boom"==q.get(j.job_id).last_error

def test_lease_recovery_and_owner():
 now=[100]; q=SQLiteProcessingQueue(clock=lambda:now[0]); j=q.enqueue(organization_id="o1",kind="x",payload={}); q.claim(worker_id="a",lease_seconds=5); now[0]=106
 assert q.recover_expired_leases()==1 and q.get(j.job_id).status is ProcessingStatus.PENDING
 q.claim(worker_id="a"); with pytest.raises(RuntimeError): q.complete(j.job_id,worker_id="b")

def test_tenant_scope():
 q=SQLiteProcessingQueue(); j=q.enqueue(organization_id="o1",kind="x",payload={})
 with pytest.raises(KeyError): q.get(j.job_id,organization_id="o2")
 with pytest.raises(KeyError): q.events(j.job_id,organization_id="o2")
