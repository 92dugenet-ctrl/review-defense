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

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def backoff_seconds(attempt: int) -> int:
    # 1m, 5m, 15m, 30m... capped to one hour.
    return min(
        3600,
        60 * (5 ** max(0, attempt - 1)),
    )


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

        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        now = self.clock()
        candidates = [
            notification
            for notification in notifications
            if (
                notification.organization_id == organization_id
                and notification.status == "PENDING"
            )
        ]
        candidates.sort(
            key=lambda notification: (
                notification.next_attempt_at
                or notification.created_at
                or "",
                notification.created_at or "",
            )
        )

        processed = 0
        sent = 0
        retried = 0
        dead = 0
        skipped = 0

        for notification in candidates[:limit]:
            due = _parse(notification.next_attempt_at)

            if due and due > now:
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

                    if audit:
                        audit(
                            organization_id,
                            actor_id,
                            "ESCALATION_NOTIFICATION_BLOCKED",
                            f"case:{notification.case_id}",
                            notification_id=notification.notification_id,
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
                    notification,
                    email_config=self.email_config,
                )
            except Exception as error:
                notification.delivery_error = str(error)

                if (
                    notification.delivery_attempts
                    >= notification.max_attempts
                ):
                    notification.dead_lettered_at = (
                        now.isoformat()
                    )
                    notification.next_attempt_at = None
                    dead += 1

                    if audit:
                        audit(
                            organization_id,
                            actor_id,
                            "ESCALATION_NOTIFICATION_DEAD_LETTERED",
                            f"case:{notification.case_id}",
                            notification_id=notification.notification_id,
                            attempts=notification.delivery_attempts,
                            error=str(error),
                        )
                else:
                    retry_at = now + timedelta(
                        seconds=backoff_seconds(
                            notification.delivery_attempts
                        )
                    )
                    notification.next_attempt_at = (
                        retry_at.isoformat()
                    )
                    retried += 1

                    if audit:
                        audit(
                            organization_id,
                            actor_id,
                            "ESCALATION_NOTIFICATION_RETRY_SCHEDULED",
                            f"case:{notification.case_id}",
                            notification_id=notification.notification_id,
                            attempts=notification.delivery_attempts,
                            next_attempt_at=notification.next_attempt_at,
                            error=str(error),
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

            if audit:
                audit(
                    organization_id,
                    actor_id,
                    "ESCALATION_NOTIFICATION_DELIVERED",
                    f"case:{notification.case_id}",
                    notification_id=notification.notification_id,
                    channel=notification.channel,
                    provider=result.provider,
                    worker=True,
                )

            if persist:
                persist(notification)

        return WorkerResult(
            processed,
            sent,
            retried,
            dead,
            skipped,
        )
