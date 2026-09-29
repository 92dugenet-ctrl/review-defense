import os
import uuid
from datetime import datetime, timezone

import pytest

from src.postgres_processing import PostgresProcessingQueue
from src.privacy_service import build_export, redact_export, validate_request_type
from src.observability import AuditChain, InMemoryTelemetry


def test_observability_is_redacted_and_tamper_evident():
    telemetry = InMemoryTelemetry()
    trace = __import__("src.observability", fromlist=["TraceContext"]).TraceContext.create(organization_id="org")
    telemetry.emit(event="test", trace=trace, fields={"token": "secret", "value": "ok"})
    assert telemetry.events[-1].fields["token"] == "[REDACTED]"
    chain = AuditChain()
    chain.append(organization_id="org", actor_id="u", action="TEST", resource_type="case", resource_id="c", trace_id=trace.trace_id)
    assert chain.verify()
    chain.records[0]["action"] = "TAMPERED"
    assert not chain.verify()


def test_privacy_export_never_contains_credentials():
    payload = build_export(
        identity={"user_id": "u", "email": "x@example.test", "password_hash": "secret"},
        reviews=[{"text": "review"}], cases=[{"case_id": "c"}],
        privacy_requests=[], consents=[], audit_events=[],
    )
    assert payload["identity"]["password_hash"] == "[REDACTED]"
    assert redact_export({"token": "abc"})["token"] == "[REDACTED]"
    assert validate_request_type("access") == "ACCESS"


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="PostgreSQL integration environment required")
def test_postgres_processing_queue_is_idempotent_and_retryable():
    import psycopg
    dsn = os.environ["DATABASE_URL"]
    with psycopg.connect(dsn) as conn:
        row = conn.execute("SELECT id FROM organizations LIMIT 1").fetchone()
        if not row:
            pytest.skip("no tenant available")
        org = str(row[0])
    queue = PostgresProcessingQueue(dsn)
    key = "integration-" + uuid.uuid4().hex
    first = queue.enqueue(organization_id=org, kind="TEST", payload={"x": 1}, idempotency_key=key)
    second = queue.enqueue(organization_id=org, kind="TEST", payload={"x": 1}, idempotency_key=key)
    assert first.job_id == second.job_id
    with pytest.raises(Exception):
        queue.enqueue(organization_id=org, kind="TEST", payload={"x": 2}, idempotency_key=key)
    worker = "test-" + uuid.uuid4().hex
    claimed = queue.claim(organization_id=org, worker_id=worker, lease_seconds=30)
    assert claimed is not None
    failed = queue.fail(org, claimed.job_id, worker, "expected test failure", retry_delay=0)
    assert failed.status.value == "pending"
    claimed = queue.claim(organization_id=org, worker_id=worker, lease_seconds=30)
    assert claimed is not None
    done = queue.complete(org, claimed.job_id, worker)
    assert done.status.value == "completed"
