"""V6.13 bounded notification delivery worker.

The worker is deliberately invocation-driven: it never starts a scheduler or thread
itself. A trusted operator or an external scheduler may invoke run_once for exactly
one tenant. Delivery remains subject to the existing V6.12 adapters and therefore
never calls Google APIs.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Callable, Iterable

from .notification_delivery import DeliveryError, deliver
from .notification_policy import NotificationPolicy, evaluate

@dataclass(frozen=True)
class WorkerResult:
    processed: int
    sent: int
    retried: int
    dead_lettered: int
    skipped: int


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def backoff_seconds(attempt: int) -> int:
    # 1m, 5m, 15m, 30m... capped to one hour.
    return min(3600, 60 * (5 ** max(0, attempt - 1)))


class NotificationWorker:
    def __init__(self, *, delivery_func=deliver, email_config=None, clock: Callable[[], datetime] = _now, policy: NotificationPolicy | None = None):
        self.delivery_func = delivery_func
        self.email_config = email_config or {}
        self.clock = clock
        self.policy = policy

    def run_once(self, notifications: Iterable, *, organization_id: str, limit: int = 25, actor_id: str | None = None,
                 persist: Callable[[object], None] | None = None, audit: Callable[..., None] | None = None) -> WorkerResult:
        if not organization_id:
            raise ValueError("organization_id is required")
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        now = self.clock()
        candidates = [n for n in notifications if n.organization_id == organization_id and n.status == "PENDING"]
        candidates.sort(key=lambda n: (n.next_attempt_at or n.created_at or "", n.created_at or ""))
        processed = sent = retried = dead = skipped = 0
        for n in candidates[:limit]:
            due = _parse(n.next_attempt_at)
            if due and due > now:
                skipped += 1
                continue
            if self.policy is not None:
                allowed, reason = evaluate(self.policy, level=n.escalation_level, channel=n.channel, now=now)
                if not allowed:
                    skipped += 1
                    if audit: audit(organization_id, actor_id, "ESCALATION_NOTIFICATION_BLOCKED", f"case:{n.case_id}", notification_id=n.notification_id, reason=reason, worker=True)
                    continue
            processed += 1
            n.delivery_attempts = getattr(n, "delivery_attempts", 0) + 1
            n.last_attempt_at = now.isoformat()
            try:
                result = self.delivery_func(n, email_config=self.email_config)
            except Exception as exc:
                n.delivery_error = str(exc)
                if n.delivery_attempts >= n.max_attempts:
                    n.dead_lettered_at = now.isoformat()
                    n.next_attempt_at = None
                    dead += 1
                    if audit: audit(organization_id, actor_id, "ESCALATION_NOTIFICATION_DEAD_LETTERED", f"case:{n.case_id}", notification_id=n.notification_id, attempts=n.delivery_attempts, error=str(exc))
                else:
                    n.next_attempt_at = (now + timedelta(seconds=backoff_seconds(n.delivery_attempts))).isoformat()
                    retried += 1
                    if audit: audit(organization_id, actor_id, "ESCALATION_NOTIFICATION_RETRY_SCHEDULED", f"case:{n.case_id}", notification_id=n.notification_id, attempts=n.delivery_attempts, next_attempt_at=n.next_attempt_at, error=str(exc))
                if persist: persist(n)
                continue
            n.status = "SENT"
            n.sent_by = actor_id
            n.sent_at = now.isoformat()
            n.delivery_error = None
            n.next_attempt_at = None
            sent += 1
            if audit: audit(organization_id, actor_id, "ESCALATION_NOTIFICATION_DELIVERED", f"case:{n.case_id}", notification_id=n.notification_id, channel=n.channel, provider=result.provider, worker=True)
            if persist: persist(n)
        return WorkerResult(processed, sent, retried, dead, skipped)
