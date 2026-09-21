"""V6.10 deterministic SLA calculations with tenant business calendars."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from .business_calendar import BusinessCalendar, default_calendar

SLA_HOURS = {"CRITICAL": 4, "HIGH": 12, "NORMAL": 24, "LOW": 72}

@dataclass(frozen=True)
class SLAStatus:
    due_at: str | None
    status: str
    remaining_hours: float | None
    sla_hours: int
    escalation: str = "NONE"
    paused: bool = False
    calendar_timezone: str = "UTC"
    business_calendar: bool = False


def _parse(value: str | None) -> datetime | None:
    if not value: return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except ValueError: return None


def calculate_sla(*, priority: str, created_at: str | None, now: datetime | None = None,
                  paused_at: str | None = None, paused_seconds: float = 0.0,
                  calendar: BusinessCalendar | None = None) -> SLAStatus:
    hours = SLA_HOURS.get(priority, SLA_HOURS["NORMAL"]); created = _parse(created_at)
    cal = calendar or default_calendar()
    if created is None: return SLAStatus(None, "UNKNOWN", None, hours, "NONE", bool(paused_at), cal.timezone, cal != default_calendar())
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc); paused_dt = _parse(paused_at)
    paused_business = max(0.0, float(paused_seconds or 0.0))
    if paused_dt is not None: paused_business += cal.business_seconds_between(paused_dt, now)
    active_seconds = max(0.0, cal.business_seconds_between(created, now) - paused_business)
    # Binary search for the wall-clock due instant in the calendar's business timeline.
    if active_seconds >= hours * 3600:
        due = now - timedelta(seconds=max(0.0, active_seconds - hours*3600))
        remaining = -(active_seconds-hours*3600)/3600
    else:
        remaining = (hours*3600-active_seconds)/3600
        due = cal.add_business_hours(now, remaining)
    paused = paused_dt is not None
    if paused: status = "PAUSED"
    elif remaining < 0: status = "OVERDUE"
    elif remaining <= max(1.0, hours*0.25): status = "DUE_SOON"
    else: status = "ON_TRACK"
    escalation = "CRITICAL" if remaining < -(hours*0.25) else "DUE" if remaining < 0 else "NONE"
    return SLAStatus(due.isoformat(), status, round(remaining,2), hours, escalation, paused, cal.timezone, cal != default_calendar())
