"""V4.9 Alert & Workflow Center.

Descriptive workflow alerts only: no policy changes and no external Google action.
Alerts are tenant-bound and generated from explicit operational conditions.
"""
from dataclasses import dataclass
from typing import Literal

AlertKind = Literal[
    "MISSING_EVIDENCE", "HUMAN_REVIEW_REQUIRED", "READY_FOR_APPROVAL",
    "SUBMISSION_TRACKING", "APPEAL_WINDOW", "URGENT_ESCALATION",
    "SLA_AT_RISK", "SLA_BREACH"
]
Priority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

ALERT_ROLES = {"OWNER", "ADMIN", "ANALYST"}
VIEW_ROLES = {"OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER"}

@dataclass(frozen=True)
class WorkflowAlert:
    alert_id: str
    organization_id: str
    case_id: str
    kind: AlertKind
    priority: Priority
    title: str
    created_at: str
    due_at: str | None = None
    source_event: str | None = None
    acknowledged_at: str | None = None
    acknowledged_by: str | None = None
    resolved_at: str | None = None
    resolved_by: str | None = None


def create_alert(*, alert_id: str, organization_id: str, case_id: str,
                 kind: AlertKind, priority: Priority, title: str,
                 created_at: str, due_at: str | None = None,
                 source_event: str | None = None) -> WorkflowAlert:
    if not all((alert_id, organization_id, case_id, title, created_at)):
        raise ValueError("alert identity fields are required")
    if kind not in {"MISSING_EVIDENCE", "HUMAN_REVIEW_REQUIRED", "READY_FOR_APPROVAL",
                    "SUBMISSION_TRACKING", "APPEAL_WINDOW", "URGENT_ESCALATION",
                    "SLA_AT_RISK", "SLA_BREACH"}:
        raise ValueError("unsupported alert kind")
    if priority not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise ValueError("unsupported priority")
    return WorkflowAlert(alert_id, organization_id, case_id, kind, priority,
                         title.strip(), created_at, due_at, source_event)


def can_view_alerts(role: str) -> bool:
    return role in VIEW_ROLES


def can_manage_alerts(role: str) -> bool:
    return role in ALERT_ROLES


def acknowledge_alert(alert: WorkflowAlert, *, actor_role: str,
                       actor_id: str, timestamp: str) -> WorkflowAlert:
    if not can_manage_alerts(actor_role):
        raise PermissionError("role cannot acknowledge alerts")
    if not actor_id or not timestamp:
        raise ValueError("actor and timestamp are required")
    if alert.resolved_at:
        raise ValueError("resolved alert cannot be acknowledged")
    return WorkflowAlert(**{**alert.__dict__, "acknowledged_at": timestamp,
                            "acknowledged_by": actor_id})


def resolve_alert(alert: WorkflowAlert, *, actor_role: str,
                  actor_id: str, timestamp: str) -> WorkflowAlert:
    if not can_manage_alerts(actor_role):
        raise PermissionError("role cannot resolve alerts")
    if not actor_id or not timestamp:
        raise ValueError("actor and timestamp are required")
    return WorkflowAlert(**{**alert.__dict__, "resolved_at": timestamp,
                            "resolved_by": actor_id})


def is_open(alert: WorkflowAlert) -> bool:
    return alert.resolved_at is None


def alert_priority(kind: AlertKind) -> Priority:
    if kind == "URGENT_ESCALATION":
        return "CRITICAL"
    if kind in {"SLA_BREACH", "APPEAL_WINDOW"}:
        return "HIGH"
    if kind in {"MISSING_EVIDENCE", "HUMAN_REVIEW_REQUIRED", "READY_FOR_APPROVAL", "SUBMISSION_TRACKING", "SLA_AT_RISK"}:
        return "MEDIUM"
    return "LOW"


def build_operational_alerts(*, organization_id: str, case_id: str,
                             created_at: str, missing_evidence: bool = False,
                             human_review: bool = False,
                             ready_for_approval: bool = False,
                             submission_tracking: bool = False,
                             appeal_window: bool = False,
                             urgent_escalation: bool = False,
                             sla_at_risk: bool = False,
                             sla_breach: bool = False,
                             due_at: str | None = None) -> tuple[WorkflowAlert, ...]:
    flags = [
        ("MISSING_EVIDENCE", missing_evidence),
        ("HUMAN_REVIEW_REQUIRED", human_review),
        ("READY_FOR_APPROVAL", ready_for_approval),
        ("SUBMISSION_TRACKING", submission_tracking),
        ("APPEAL_WINDOW", appeal_window),
        ("URGENT_ESCALATION", urgent_escalation),
        ("SLA_AT_RISK", sla_at_risk),
        ("SLA_BREACH", sla_breach),
    ]
    alerts = []
    for kind, active in flags:
        if active:
            alerts.append(create_alert(
                alert_id=f"{case_id}:{kind}", organization_id=organization_id,
                case_id=case_id, kind=kind, priority=alert_priority(kind),
                title=kind.replace("_", " ").title(), created_at=created_at,
                due_at=due_at, source_event="CASE_WORKFLOW"))
    return tuple(alerts)


def summarize_alerts(alerts: tuple[WorkflowAlert, ...] | list[WorkflowAlert]) -> dict[str, int]:
    return {
        "total": len(alerts),
        "open": sum(is_open(a) for a in alerts),
        "critical": sum(a.priority == "CRITICAL" and is_open(a) for a in alerts),
        "high": sum(a.priority == "HIGH" and is_open(a) for a in alerts),
        "sla": sum(a.kind in {"SLA_AT_RISK", "SLA_BREACH"} and is_open(a) for a in alerts),
    }
