"""Bounded, tenant-scoped notification delivery worker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

from .notification_delivery import deliver
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
    """Return the capped retry delay for a delivery attempt."""
    return min(3600, 60 * (5 ** max(0, attempt - 1)))


class NotificationWorker:
    def __init__(
        self,
        *,
        delivery_func=deliver,
        email_config=None,
        clock: Callable[[], datetime] = _now,
        policy: NotificationPolicy | None = None,
    ):
        self.delivery_func = delivery_func
        self.email_config = email_config or {}
        self.clock = clock
        self.policy = policy

    def run_once(
        self,
        notifications: Iterable,
        *,
        organization_id: str,
        limit: int = 25,
        actor_id: str | None = None,
        persist: Callable[[object], None] | None = None,
        audit: Callable[..., None] | None = None,
    ) -> WorkerResult:
        if not organization_id:
            raise ValueError("organization_id is required")
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")

        now = self.clock()
        candidates = [
            notification
            for notification in notifications
            if notification.organization_id == organization_id
            and notification.status == "PENDING"
        ]
        candidates.sort(
            key=lambda notification: (
                notification.next_attempt_at or notification.created_at or "",
                notification.created_at or "",
            )
        )

        processed = sent = retried = dead_lettered = skipped = 0

        for notification in candidates[:limit]:
            due_at = _parse(notification.next_attempt_at)
            if due_at and due_at > now:
                skipped += 1
                continue

            if self.policy is not None:
                allowed, reason = evaluate(
                    self.policy,
                    level=notification.escalation_level,
                    channel=notification.channel,
                    now=now,
                )
                if not allowed:
                    skipped += 1
                    self._audit(
                        audit,
                        organization_id,
                        actor_id,
                        "ESCALATION_NOTIFICATION_BLOCKED",
                        notification,
                        reason=reason,
                        worker=True,
                    )
                    continue

            processed += 1
            notification.delivery_attempts = (
                getattr(notification, "delivery_attempts", 0) + 1
            )
            notification.last_attempt_at = now.isoformat()

            try:
                result = self.delivery_func(
                    notification, email_config=self.email_config
                )
            except Exception as error:
                notification.delivery_error = str(error)
                if notification.delivery_attempts >= notification.max_attempts:
                    notification.dead_lettered_at = now.isoformat()
                    notification.next_attempt_at = None
                    dead_lettered += 1
                    event = "ESCALATION_NOTIFICATION_DEAD_LETTERED"
                    details = {"attempts": notification.delivery_attempts}
                else:
                    notification.next_attempt_at = (
                        now
                        + timedelta(
                            seconds=backoff_seconds(notification.delivery_attempts)
                        )
                    ).isoformat()
                    retried += 1
                    event = "ESCALATION_NOTIFICATION_RETRY_SCHEDULED"
                    details = {
                        "attempts": notification.delivery_attempts,
                        "next_attempt_at": notification.next_attempt_at,
                    }

                self._audit(
                    audit,
                    organization_id,
                    actor_id,
                    event,
                    notification,
                    error=str(error),
                    **details,
                )
                if persist:
                    persist(notification)
                continue

            notification.status = "SENT"
            notification.sent_by = actor_id
            notification.sent_at = now.isoformat()
            notification.delivery_error = None
            notification.next_attempt_at = None
            sent += 1
            self._audit(
                audit,
                organization_id,
                actor_id,
                "ESCALATION_NOTIFICATION_DELIVERED",
                notification,
                channel=notification.channel,
                provider=result.provider,
                worker=True,
            )
            if persist:
                persist(notification)

        return WorkerResult(processed, sent, retried, dead_lettered, skipped)

    @staticmethod
    def _audit(audit, organization_id, actor_id, event, notification, **details):
        if audit:
            audit(
                organization_id,
                actor_id,
                event,
                f"case:{notification.case_id}",
                notification_id=notification.notification_id,
                **details,
            )
