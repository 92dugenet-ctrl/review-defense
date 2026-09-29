"""V6.11 auditable escalation notification outbox.

Notifications are queued only. This module deliberately performs no network I/O and
cannot mutate Google resources. A separate, explicitly authorized delivery adapter
may consume the outbox in a future release.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import uuid

ALLOWED_CHANNELS = {"IN_APP", "EMAIL", "WEBHOOK"}
ALLOWED_STATUSES = {"PENDING", "SENT", "CANCELLED"}

@dataclass
class Notification:
    notification_id: str
    organization_id: str
    case_id: str
    escalation_level: str
    channel: str
    target: str
    subject: str
    body: str
    status: str = "PENDING"
    created_by: str | None = None
    created_at: str | None = None
    sent_by: str | None = None
    sent_at: str | None = None
    cancelled_by: str | None = None
    cancelled_at: str | None = None
    dedupe_key: str | None = None
    delivery_attempts: int = 0
    last_attempt_at: str | None = None
    delivery_error: str | None = None
    max_attempts: int = 3
    next_attempt_at: str | None = None
    dead_lettered_at: str | None = None

    def payload(self):
        return asdict(self)


def make_dedupe_key(organization_id: str, case_id: str, level: str, channel: str, target: str) -> str:
    raw = "|".join([organization_id, case_id, level, channel.upper(), target.strip().lower()])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_notification(*, organization_id: str, case_id: str, level: str, channel: str,
                         target: str, subject: str, body: str, actor_id: str) -> Notification:
    channel = channel.strip().upper()
    if channel not in ALLOWED_CHANNELS:
        raise ValueError("unsupported notification channel")
    if not target.strip():
        raise ValueError("notification target is required")
    if not subject.strip() or not body.strip():
        raise ValueError("notification subject and body are required")
    now = datetime.now(timezone.utc).isoformat()
    return Notification(
        notification_id=str(uuid.uuid4()), organization_id=organization_id,
        case_id=case_id, escalation_level=level, channel=channel,
        target=target.strip(), subject=subject.strip(), body=body,
        created_by=actor_id, created_at=now,
        dedupe_key=make_dedupe_key(organization_id, case_id, level, channel, target),
    )
