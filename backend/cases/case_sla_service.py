"""Cases SLA application seam.

Owns SLA calculation and the existing pause/resume persistence side effects.
HTTP parsing, authorization, validation and error translation remain in the API.
"""
from __future__ import annotations

from typing import Any, Callable

from ..reviews.review_sla import SLAStatus, calculate_sla
from ..authentication.security_hardening import utc_now
from ..api.business_calendar import BusinessCalendar


class CaseSLAService:
    """Application boundary for case SLA calculations and controls."""

    def __init__(self, *, repository: Any = None, audit_event: Callable[..., Any] | None = None):
        self.repository = repository
        self.audit_event = audit_event

    def calculate(self, case: Any, priority: str, calendar: BusinessCalendar) -> SLAStatus:
        return calculate_sla(
            priority=priority,
            created_at=case.created_at,
            paused_at=case.sla_paused_at,
            paused_seconds=case.sla_paused_seconds,
            calendar=calendar,
        )

    def pause(self, case: Any, organization_id: str, user_id: str, reason: str) -> dict[str, Any]:
        case.sla_paused_at = utc_now().isoformat()
        case.sla_pause_reason = reason
        if self.repository is not None:
            self.repository.update_case_sla(
                organization_id,
                case.case_id,
                paused_at=case.sla_paused_at,
                paused_seconds=case.sla_paused_seconds,
                pause_reason=reason,
            )
        if self.audit_event is not None:
            self.audit_event(
                organization_id,
                user_id,
                "CASE_SLA_PAUSED",
                f"case:{case.case_id}",
                reason=reason,
            )
        return {
            "case_id": case.case_id,
            "sla_paused_at": case.sla_paused_at,
            "reason": reason,
        }

    def resume(self, case: Any, organization_id: str, user_id: str, calendar: BusinessCalendar) -> dict[str, Any]:
        paused_at = __import__("datetime").datetime.fromisoformat(case.sla_paused_at.replace("Z", "+00:00"))
        if paused_at.tzinfo is None:
            paused_at = paused_at.replace(tzinfo=__import__("datetime").timezone.utc)
        now_dt = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        case.sla_paused_seconds += calendar.business_seconds_between(paused_at, now_dt)
        case.sla_paused_at = None
        case.sla_pause_reason = None
        if self.repository is not None:
            self.repository.update_case_sla(
                organization_id,
                case.case_id,
                paused_at=None,
                paused_seconds=case.sla_paused_seconds,
                pause_reason=None,
            )
        if self.audit_event is not None:
            self.audit_event(
                organization_id,
                user_id,
                "CASE_SLA_RESUMED",
                f"case:{case.case_id}",
                paused_seconds=round(case.sla_paused_seconds, 2),
            )
        return {
            "case_id": case.case_id,
            "sla_paused_seconds": round(case.sla_paused_seconds, 2),
        }
