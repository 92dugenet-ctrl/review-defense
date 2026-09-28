from src.observability import InMemoryTelemetry
from src.ops_alerts import evaluate_alerts

def test_alerts_fire_when_not_ready():
    t=InMemoryTelemetry(); t.increment("http_requests_total", value=25); t.increment("http_errors_total", value=2)
    alerts=evaluate_alerts(counters=t.counters, readiness_ok=False)
    assert next(a for a in alerts if a.name=="service_not_ready").status=="firing"
    assert next(a for a in alerts if a.name=="http_5xx_ratio").status=="firing"

def test_alerts_are_non_remediating():
    alerts=evaluate_alerts(counters={}, readiness_ok=True)
    assert all(a.status=="ok" for a in alerts)
