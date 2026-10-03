"""Tenant-configurable business calendar and business-hour arithmetic."""

from __future__ import annotations

from dataclasses import dataclass
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
            try:
                ZoneInfo(self.timezone)
            except Exception as exc:
                raise ValueError("invalid timezone") from exc

        if not self.workdays or any(
            day < 0 or day > 6 for day in self.workdays
        ):
            raise ValueError("invalid workdays")

        if not (0 <= self.start_hour < self.end_hour <= 24):
            raise ValueError("invalid business hours")

        for holiday in self.holidays:
            try:
                date.fromisoformat(holiday)
            except ValueError as exc:
                raise ValueError("invalid holiday") from exc

        return self

    def is_business_day(self, day: date) -> bool:
        return (
            day.weekday() in self.workdays
            and day.isoformat() not in set(self.holidays)
        )

    def _window(self, day: date):
        timezone_info = ZoneInfo(self.timezone)
        start = datetime.combine(
            day,
            time(self.start_hour),
            tzinfo=timezone_info,
        )

        if self.end_hour == 24:
            end = datetime.combine(
                day,
                time(0),
                tzinfo=timezone_info,
            ) + timedelta(days=1)
        else:
            end = datetime.combine(
                day,
                time(self.end_hour),
                tzinfo=timezone_info,
            )

        return start, end

    def business_seconds_between(
        self,
        start: datetime,
        end: datetime,
    ) -> float:
        if end <= start:
            return 0.0

        timezone_info = ZoneInfo(self.timezone)
        start = start.astimezone(timezone_info)
        end = end.astimezone(timezone_info)

        total_seconds = 0.0
        current_day = start.date()

        while current_day <= end.date():
            if self.is_business_day(current_day):
                window_start, window_end = self._window(current_day)
                overlap_start = max(start, window_start)
                overlap_end = min(end, window_end)

                if overlap_end > overlap_start:
                    total_seconds += (
                        overlap_end - overlap_start
                    ).total_seconds()

            current_day += timedelta(days=1)

        return total_seconds

    def add_business_hours(
        self,
        start: datetime,
        hours: float,
    ) -> datetime:
        if hours <= 0:
            return start

        timezone_info = ZoneInfo(self.timezone)
        cursor = start.astimezone(timezone_info)
        remaining_seconds = hours * 3600

        while True:
            if self.is_business_day(cursor.date()):
                window_start, window_end = self._window(cursor.date())

                if cursor < window_start:
                    cursor = window_start

                if window_start <= cursor < window_end:
                    available_seconds = (
                        window_end - cursor
                    ).total_seconds()

                    if remaining_seconds <= available_seconds:
                        return (
                            cursor + timedelta(seconds=remaining_seconds)
                        ).astimezone(timezone.utc)

                    remaining_seconds -= available_seconds

            cursor = datetime.combine(
                cursor.date() + timedelta(days=1),
                time(0),
                tzinfo=timezone_info,
            )


def default_calendar() -> BusinessCalendar:
    """Preserve elapsed-time semantics until a tenant sets office hours."""
    return BusinessCalendar(
        timezone="UTC",
        workdays=(0, 1, 2, 3, 4, 5, 6),
        start_hour=0,
        end_hour=24,
    )


def calendar_from_dict(data: dict | None) -> BusinessCalendar:
    data = data or {}
    calendar = BusinessCalendar(
        timezone=str(data.get("timezone", "UTC")),
        workdays=tuple(
            int(day)
            for day in data.get("workdays", (0, 1, 2, 3, 4, 5, 6))
        ),
        start_hour=int(data.get("start_hour", 0)),
        end_hour=int(data.get("end_hour", 24)),
        holidays=tuple(
            str(holiday)
            for holiday in data.get("holidays", ())
        ),
    )
    return calendar.validate()
