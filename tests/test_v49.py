import pytest
from src.alert_workspace import (
    create_alert, can_view_alerts, can_manage_alerts, acknowledge_alert,
    resolve_alert, is_open, alert_priority, build_operational_alerts,
    summarize_alerts,
)


def make(kind="MISSING_EVIDENCE"):
    return create_alert(alert_id="a1", organization_id="org-a", case_id="c1",
                        kind=kind, priority=alert_priority(kind), title="Need evidence",
                        created_at="2026-09-20T14:00:00Z")


def test_create_and_priority():
    assert make().priority == "MEDIUM"
    assert make("URGENT_ESCALATION").priority == "CRITICAL"
    assert make("SLA_BREACH").priority == "HIGH"


def test_permissions():
    assert can_view_alerts("CLIENT")
    assert can_view_alerts("VIEWER")
    assert can_manage_alerts("ADMIN")
    assert not can_manage_alerts("CLIENT")


def test_acknowledge_and_resolve():
    a = make()
    a = acknowledge_alert(a, actor_role="ANALYST", actor_id="u1", timestamp="t1")
    assert a.acknowledged_by == "u1"
    a = resolve_alert(a, actor_role="ADMIN", actor_id="u2", timestamp="t2")
    assert not is_open(a)
    assert a.resolved_by == "u2"


def test_client_cannot_manage():
    with pytest.raises(PermissionError):
        acknowledge_alert(make(), actor_role="CLIENT", actor_id="u", timestamp="t")


def test_resolved_cannot_acknowledge():
    a = resolve_alert(make(), actor_role="ADMIN", actor_id="u", timestamp="t2")
    with pytest.raises(ValueError):
        acknowledge_alert(a, actor_role="ADMIN", actor_id="u", timestamp="t3")


def test_invalid_alert():
    with pytest.raises(ValueError):
        create_alert(alert_id="", organization_id="o", case_id="c", kind="BAD",
                     priority="LOW", title="x", created_at="t")


def test_builder_only_creates_active_alerts():
    alerts = build_operational_alerts(organization_id="o", case_id="c", created_at="t",
                                      missing_evidence=True, human_review=True,
                                      urgent_escalation=True)
    assert [a.kind for a in alerts] == ["MISSING_EVIDENCE", "HUMAN_REVIEW_REQUIRED", "URGENT_ESCALATION"]
    assert alerts[-1].priority == "CRITICAL"


def test_summary():
    alerts = build_operational_alerts(organization_id="o", case_id="c", created_at="t",
                                      urgent_escalation=True, sla_breach=True)
    assert summarize_alerts(alerts) == {"total": 2, "open": 2, "critical": 1, "high": 1, "sla": 1}


def test_tenant_identity():
    a = make()
    assert a.organization_id == "org-a"
    assert a.case_id == "c1"
