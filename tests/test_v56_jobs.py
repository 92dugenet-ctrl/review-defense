import threading

import pytest

from src.background_jobs import (
    JobIdempotencyConflict, JobNotFound, JobState, JobWorker, SQLiteJobQueue,
)


def test_enqueue_claim_and_success_are_persistent(tmp_path):
    path = tmp_path / "jobs.sqlite"
    q1 = SQLiteJobQueue(str(path))
    job = q1.enqueue(organization_id="org-a", kind="analyze", payload={"review_id": "r1"}, priority=5)
    claimed = q1.claim(worker_id="w1")
    assert claimed and claimed.id == job.id and claimed.state == JobState.RUNNING
    done = q1.succeed(job.id, worker_id="w1")
    assert done.state == JobState.SUCCEEDED
    q1.close()
    q2 = SQLiteJobQueue(str(path))
    assert q2.get(job.id, organization_id="org-a").state == JobState.SUCCEEDED


def test_priority_ordering():
    q = SQLiteJobQueue()
    low = q.enqueue(organization_id="org-a", kind="x", payload={"n": 1}, priority=1)
    high = q.enqueue(organization_id="org-a", kind="x", payload={"n": 2}, priority=10)
    assert q.claim(worker_id="w").id == high.id
    assert q.claim(worker_id="w").id == low.id


def test_idempotency_returns_existing_job_and_rejects_changed_payload():
    q = SQLiteJobQueue()
    first = q.enqueue(organization_id="org-a", kind="x", payload={"a": 1}, idempotency_key="k")
    second = q.enqueue(organization_id="org-a", kind="x", payload={"a": 1}, idempotency_key="k")
    assert second.id == first.id
    with pytest.raises(JobIdempotencyConflict):
        q.enqueue(organization_id="org-a", kind="x", payload={"a": 2}, idempotency_key="k")


def test_idempotency_is_tenant_scoped():
    q = SQLiteJobQueue()
    a = q.enqueue(organization_id="org-a", kind="x", payload={"a": 1}, idempotency_key="k")
    b = q.enqueue(organization_id="org-b", kind="x", payload={"a": 2}, idempotency_key="k")
    assert a.id != b.id
    with pytest.raises(JobNotFound):
        q.get(a.id, organization_id="org-b")


def test_failure_retries_then_dead_letters():
    q = SQLiteJobQueue()
    job = q.enqueue(organization_id="org-a", kind="x", payload={}, max_attempts=2)
    running = q.claim(worker_id="w")
    retry = q.fail(running.id, worker_id="w", error="temporary", retry_delay=0)
    assert retry.state == JobState.RETRY_SCHEDULED
    running2 = q.claim(worker_id="w")
    dead = q.fail(running2.id, worker_id="w", error="permanent", retry_delay=0)
    assert dead.state == JobState.DEAD_LETTER
    assert [j.id for j in q.dead_letters(organization_id="org-a")] == [job.id]


def test_expired_lease_is_recoverable():
    clock = [100.0]
    q = SQLiteJobQueue(clock=lambda: clock[0])
    job = q.enqueue(organization_id="org-a", kind="x", payload={})
    assert q.claim(worker_id="dead-worker", lease_seconds=5).id == job.id
    clock[0] = 106.0
    assert q.recover_expired_leases() == 1
    recovered = q.claim(worker_id="live-worker")
    assert recovered.id == job.id and recovered.state == JobState.RUNNING


def test_worker_handles_success_and_handler_error():
    q = SQLiteJobQueue()
    seen = []
    ok = q.enqueue(organization_id="org-a", kind="ok", payload={"x": 1})
    bad = q.enqueue(organization_id="org-a", kind="bad", payload={}, max_attempts=1)
    worker = JobWorker(q, {"ok": lambda p: seen.append(p), "bad": lambda p: (_ for _ in ()).throw(ValueError("boom"))}, worker_id="w", retry_delay=0)
    assert worker.run_once().state == JobState.SUCCEEDED
    assert worker.run_once().state == JobState.DEAD_LETTER
    assert seen == [{"x": 1}]


def test_worker_no_handler_dead_letters_after_budget():
    q = SQLiteJobQueue()
    job = q.enqueue(organization_id="org-a", kind="unknown", payload={}, max_attempts=1)
    result = JobWorker(q, {}, worker_id="w").run_once()
    assert result.id == job.id and result.state == JobState.DEAD_LETTER


def test_concurrent_claim_only_one_worker_gets_job():
    q = SQLiteJobQueue()
    job = q.enqueue(organization_id="org-a", kind="x", payload={})
    results = []
    lock = threading.Lock()

    def claim():
        result = q.claim(worker_id=threading.current_thread().name)
        with lock:
            results.append(result)

    threads = [threading.Thread(target=claim, name=f"w{i}") for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    claimed = [r for r in results if r is not None]
    assert len(claimed) == 1
    assert claimed[0].id == job.id


def test_cancel_requires_tenant_and_cannot_cancel_running():
    q = SQLiteJobQueue()
    job = q.enqueue(organization_id="org-a", kind="x", payload={})
    with pytest.raises(JobNotFound):
        q.cancel(job.id, organization_id="org-b")
    assert q.cancel(job.id, organization_id="org-a").state == JobState.CANCELLED
    job2 = q.enqueue(organization_id="org-a", kind="x", payload={})
    q.claim(worker_id="w")
    with pytest.raises(RuntimeError):
        q.cancel(job2.id, organization_id="org-a")
