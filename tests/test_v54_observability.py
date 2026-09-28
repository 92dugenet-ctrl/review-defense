from src.observability import (
    AuditChain, InMemoryTelemetry, TraceContext, health_check, measure, readiness_check,
    redact,
)


def test_structured_event_is_json_and_redacts_sensitive_payloads():
    telemetry = InMemoryTelemetry()
    trace = TraceContext.create(organization_id="org-a", actor_id="u1")
    event = telemetry.emit(event="case.created", trace=trace, fields={
        "case_id": "c1", "password": "secret", "review_text": "private review",
        "size": 12,
    })
    data = event.as_dict()
    assert data["fields"]["password"] == "[REDACTED]"
    assert data["fields"]["review_text"] == "[REDACTED]"
    assert '"case_id":"c1"' in event.to_json()
    assert event.trace_id == trace.trace_id


def test_metrics_count_and_latency_are_recorded():
    telemetry = InMemoryTelemetry()
    wrapped = measure(lambda: 42, telemetry, metric_name="review.ingest", labels={"tenant": "org-a"})
    assert wrapped() == 42
    assert telemetry.metric("review.ingest.success", labels={"tenant": "org-a"}) == 1
    stats = telemetry.timing_stats("review.ingest", labels={"tenant": "org-a"})
    assert stats["count"] == 1
    assert stats["max_ms"] >= 0


def test_errors_increment_error_metric_and_are_not_swallowed():
    telemetry = InMemoryTelemetry()
    def boom():
        raise ValueError("bad input")
    wrapped = measure(boom, telemetry, metric_name="review.analyze")
    try:
        wrapped()
    except ValueError:
        pass
    else:
        assert False
    assert telemetry.metric("review.analyze.error", labels={"error": "ValueError"}) == 1


def test_audit_chain_is_tamper_evident():
    chain = AuditChain()
    chain.append(organization_id="org-a", actor_id="u1", action="CASE_CREATED",
                 resource_type="case", resource_id="c1", trace_id="t1", metadata={"note": "ok"})
    chain.append(organization_id="org-a", actor_id="u1", action="APPROVED",
                 resource_type="decision", resource_id="d1", trace_id="t1")
    assert chain.verify()
    chain.records[0]["action"] = "TAMPERED"
    assert not chain.verify()


def test_audit_chain_does_not_store_raw_sensitive_values():
    chain = AuditChain()
    record = chain.append(organization_id="org-a", actor_id="u1", action="UPLOAD",
                          resource_type="evidence", resource_id="e1", trace_id="t1",
                          metadata={"content": b"secret bytes", "token": "abc"})
    assert record["metadata"]["content"] == "[REDACTED]"
    assert record["metadata"]["token"] == "[REDACTED]"
    assert chain.verify()


def test_health_and_readiness_report_component_failures():
    healthy = health_check(checks={"db": lambda: True, "vault": lambda: True})
    assert healthy.status == "ok"
    assert healthy.checks == {"db": "ok", "vault": "ok"}
    ready = readiness_check(checks={"db": lambda: True, "google": lambda: False})
    assert ready.status == "failed"
    assert ready.checks["google"] == "failed"


def test_health_exception_is_reported_without_leaking_exception_text():
    def broken():
        raise RuntimeError("database password=supersecret")
    result = health_check(checks={"db": broken})
    assert result.status == "failed"
    assert result.checks == {"db": "error"}


def test_redact_limits_large_values_and_nested_data():
    result = redact({"safe": "x" * 1000, "nested": {"token": "secret", "ok": 1}})
    assert len(result["safe"]) == 513
    assert result["nested"]["token"] == "[REDACTED]"
    assert result["nested"]["ok"] == 1
