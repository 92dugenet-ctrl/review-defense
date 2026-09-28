"""Application service for Cases operational controls."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Callable


class CaseOperationsService:
    def __init__(self, *, store: Any, repository: Any = None,
                 audit_event: Callable[..., Any] | None = None):
        self.store = store
        self.repository = repository
        self.audit_event = audit_event

    def assign(self, *, case: Any, user_id: str) -> None:
        case.assigned_to = user_id
        self.store.case_assignments[(case.organization_id, case.case_id)] = user_id
        if self.repository is not None and hasattr(self.repository, "assign_case"):
            self.repository.assign_case(case.organization_id, case.case_id, user_id)
        if self.audit_event is not None:
            self.audit_event(case.organization_id, user_id, "CASE_ASSIGNED",
                             f"case:{case.case_id}", assignee_id=user_id)

    def unassign(self, *, case: Any, user_id: str) -> None:
        case.assigned_to = None
        self.store.case_assignments[(case.organization_id, case.case_id)] = None
        if self.repository is not None and hasattr(self.repository, "assign_case"):
            self.repository.assign_case(case.organization_id, case.case_id, None)
        if self.audit_event is not None:
            self.audit_event(case.organization_id, user_id, "CASE_UNASSIGNED",
                             f"case:{case.case_id}")

    def pause_sla(self, *, case: Any, user_id: str, reason: str, paused_at: str) -> None:
        if case.sla_paused_at:
            raise ValueError("SLA is already paused")
        case.sla_paused_at = paused_at
        case.sla_pause_reason = reason
        if self.repository is not None and hasattr(self.repository, "update_case_sla"):
            self.repository.update_case_sla(
                case.organization_id, case.case_id,
                paused_at=paused_at,
                paused_seconds=case.sla_paused_seconds,
                pause_reason=reason,
            )
        if self.audit_event is not None:
            self.audit_event(case.organization_id, user_id, "CASE_SLA_PAUSED",
                             f"case:{case.case_id}", reason=reason)

    def resume_sla(self, *, case: Any, user_id: str, calendar: Any,
                   now: datetime) -> float:
        if not case.sla_paused_at:
            raise ValueError("SLA is not paused")
        paused_at = datetime.fromisoformat(case.sla_paused_at.replace("Z", "+00:00"))
        if paused_at.tzinfo is None:
            paused_at = paused_at.replace(tzinfo=timezone.utc)
        case.sla_paused_seconds += calendar.business_seconds_between(paused_at, now)
        case.sla_paused_at = None
        case.sla_pause_reason = None
        if self.repository is not None and hasattr(self.repository, "update_case_sla"):
            self.repository.update_case_sla(
                case.organization_id, case.case_id,
                paused_at=None,
                paused_seconds=case.sla_paused_seconds,
                pause_reason=None,
            )
        if self.audit_event is not None:
            self.audit_event(case.organization_id, user_id, "CASE_SLA_RESUMED",
                             f"case:{case.case_id}",
                             paused_seconds=round(case.sla_paused_seconds, 2))
        return round(case.sla_paused_seconds, 2)
