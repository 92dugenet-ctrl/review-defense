"""V6.14 tenant-scoped notification policy controls.

Policies constrain escalation notifications before they enter the outbox. They are
configuration only: they never invoke external services and cannot bypass Google
human-approval gates.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, time
from zoneinfo import ZoneInfo

LEVELS = {"DUE", "CRITICAL"}
CHANNELS = {"IN_APP", "EMAIL", "WEBHOOK"}

@dataclass(frozen=True)
class NotificationPolicy:
    organization_id: str
    enabled: bool = True
    levels: tuple[str, ...] = ("DUE", "CRITICAL")
    channels: tuple[str, ...] = ("IN_APP", "EMAIL", "WEBHOOK")
    quiet_start: str | None = None
    quiet_end: str | None = None
    allow_external: bool = True

    def payload(self):
        d = asdict(self)
        d["levels"] = list(self.levels)
        d["channels"] = list(self.channels)
        return d


def validate_policy(organization_id: str, data: dict) -> NotificationPolicy:
    if not organization_id:
        raise ValueError("organization_id is required")
    levels = tuple(str(x).upper() for x in data.get("levels", ["DUE", "CRITICAL"]))
    channels = tuple(str(x).upper() for x in data.get("channels", ["IN_APP", "EMAIL", "WEBHOOK"]))
    if not levels or any(x not in LEVELS for x in levels):
        raise ValueError("levels must contain only DUE or CRITICAL")
    if not channels or any(x not in CHANNELS for x in channels):
        raise ValueError("channels contain an unsupported value")
    qs, qe = data.get("quiet_start"), data.get("quiet_end")
    for value in (qs, qe):
        if value is not None:
            try: time.fromisoformat(str(value))
            except ValueError as exc: raise ValueError("quiet hours must use HH:MM[:SS]") from exc
    return NotificationPolicy(organization_id, bool(data.get("enabled", True)), levels, channels, qs, qe, bool(data.get("allow_external", True)))


def _in_quiet_window(now: datetime, start: str | None, end: str | None) -> bool:
    if not start or not end:
        return False
    current = now.timetz().replace(tzinfo=None)
    s, e = time.fromisoformat(start), time.fromisoformat(end)
    return (s <= current < e) if s <= e else (current >= s or current < e)


def evaluate(policy: NotificationPolicy, *, level: str, channel: str, now: datetime | None = None) -> tuple[bool, str]:
    level, channel = level.upper(), channel.upper()
    if not policy.enabled: return False, "notification policy disabled"
    if level not in policy.levels: return False, "escalation level is not enabled by policy"
    if channel not in policy.channels: return False, "notification channel is not enabled by policy"
    if channel in {"EMAIL", "WEBHOOK"} and not policy.allow_external:
        return False, "external notification delivery is disabled by policy"
    if now is not None:
        try: local = now.astimezone(ZoneInfo("UTC"))
        except Exception: local = now
        if _in_quiet_window(local, policy.quiet_start, policy.quiet_end):
            return False, "notification is inside the configured quiet window"
    return True, "allowed"
