"""V6.10 auditable escalation signals with explicit human acknowledgement/resolution."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class Escalation:
    case_id: str
    level: str
    reason: str
    status: str = "OPEN"
    acknowledged_by: str | None = None
    acknowledged_at: str | None = None
    resolved_by: str | None = None
    resolved_at: str | None = None

    def payload(self): return asdict(self)


def signal_from_sla(case_id: str, sla) -> Escalation | None:
    if sla.escalation == "NONE": return None
    reason = "SLA breached" if sla.escalation == "DUE" else "SLA materially overdue"
    return Escalation(case_id, sla.escalation, reason)
