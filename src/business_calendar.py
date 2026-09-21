"""V6.10 tenant-configurable business calendar and business-hour arithmetic."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

@dataclass(frozen=True)
class BusinessCalendar:
    timezone: str = "UTC"
    workdays: tuple[int, ...] = (0, 1, 2, 3, 4)
    start_hour: int = 9
    end_hour: int = 17
    holidays: tuple[str, ...] = ()

    def validate(self) -> "BusinessCalendar":
        if self.timezone not in {"UTC"}:
            try: ZoneInfo(self.timezone)
            except Exception as exc: raise ValueError("invalid timezone") from exc
        if not self.workdays or any(d < 0 or d > 6 for d in self.workdays): raise ValueError("invalid workdays")
        if not (0 <= self.start_hour < self.end_hour <= 24): raise ValueError("invalid business hours")
        for h in self.holidays:
            try: date.fromisoformat(h)
            except ValueError as exc: raise ValueError("invalid holiday") from exc
        return self

    def is_business_day(self, d: date) -> bool:
        return d.weekday() in self.workdays and d.isoformat() not in set(self.holidays)

    def _window(self, d: date):
        tz = ZoneInfo(self.timezone)
        start = datetime.combine(d, time(self.start_hour), tzinfo=tz)
        end = datetime.combine(d, time(0), tzinfo=tz) + timedelta(days=1) if self.end_hour == 24 else datetime.combine(d, time(self.end_hour), tzinfo=tz)
        return start, end

    def business_seconds_between(self, start: datetime, end: datetime) -> float:
        if end <= start: return 0.0
        tz = ZoneInfo(self.timezone)
        start = start.astimezone(tz); end = end.astimezone(tz)
        total = 0.0; cursor = start.date()
        while cursor <= end.date():
            if self.is_business_day(cursor):
                ws, we = self._window(cursor)
                left, right = max(start, ws), min(end, we)
                if right > left: total += (right-left).total_seconds()
            cursor += timedelta(days=1)
        return total

    def add_business_hours(self, start: datetime, hours: float) -> datetime:
        if hours <= 0: return start
        tz = ZoneInfo(self.timezone); cursor = start.astimezone(tz); remaining = hours * 3600
        while True:
            if self.is_business_day(cursor.date()):
                ws, we = self._window(cursor.date())
                if cursor < ws: cursor = ws
                if ws <= cursor < we:
                    available = (we-cursor).total_seconds()
                    if remaining <= available: return (cursor + timedelta(seconds=remaining)).astimezone(timezone.utc)
                    remaining -= available
            cursor = datetime.combine(cursor.date()+timedelta(days=1), time(0), tzinfo=tz)


def default_calendar() -> BusinessCalendar:
    # 24/7 default preserves the pre-V6.10 elapsed-time semantics until a tenant configures office hours.
    return BusinessCalendar(timezone="UTC", workdays=(0,1,2,3,4,5,6), start_hour=0, end_hour=24)


def calendar_from_dict(data: dict | None) -> BusinessCalendar:
    data = data or {}
    cal = BusinessCalendar(
        timezone=str(data.get("timezone", "UTC")),
        workdays=tuple(int(x) for x in data.get("workdays", (0,1,2,3,4,5,6))),
        start_hour=int(data.get("start_hour", 0)), end_hour=int(data.get("end_hour", 24)),
        holidays=tuple(str(x) for x in data.get("holidays", ())),
    )
    return cal.validate()
