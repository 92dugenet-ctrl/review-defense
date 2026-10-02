"""PostgreSQL-backed notification outbox worker.

Delivery is injected, so production can use the existing controlled delivery
adapter while tests remain network-free. Claims use SKIP LOCKED for concurrency.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Callable, Any

import psycopg

from .notification_outbox import Notification
from .notification_worker import backoff_seconds


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class NotificationRun:
    processed: int
    sent: int
    retried: int
    dead_lettered: int


class PostgresNotificationWorker:
    def __init__(self, dsn: str, *, delivery_func: Callable[..., Any]):
        self.dsn = dsn
        self.delivery_func = delivery_func

    def run_once(self, *, organization_id: str, limit: int = 25, actor_id: str | None = None,
                 email_config: dict[str, Any] | None = None) -> NotificationRun:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        processed = sent = retried = dead = 0
        now = _now()
        with psycopg.connect(self.dsn, connect_timeout=5) as conn:
            with conn.transaction():
                conn.execute("SELECT set_config('app.organization_id', %s, true)", (organization_id,))
                rows = conn.execute(
                    """SELECT organization_id,notification_id,case_id,escalation_level,channel,target,
                       subject,body,status,created_by,created_at,sent_by,sent_at,cancelled_by,cancelled_at,
                       dedupe_key,delivery_attempts,last_attempt_at,delivery_error,max_attempts,next_attempt_at,dead_lettered_at
                       FROM notification_outbox
                       WHERE organization_id=%s AND status='PENDING'
                         AND (next_attempt_at IS NULL OR next_attempt_at<=%s)
                       ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT %s""",
                    (organization_id, now, limit),
                ).fetchall()
                for row in rows:
                    processed += 1
                    n = Notification(
                        notification_id=str(row[1]), organization_id=str(row[0]), case_id=str(row[2]),
                        escalation_level=row[3], channel=row[4], target=row[5], subject=row[6], body=row[7],
                        status=row[8], created_by=str(row[9]) if row[9] else None,
                        created_at=row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10]),
                        sent_by=str(row[11]) if row[11] else None,
                        sent_at=row[12].isoformat() if hasattr(row[12], "isoformat") else None,
                        cancelled_by=str(row[13]) if row[13] else None,
                        cancelled_at=row[14].isoformat() if hasattr(row[14], "isoformat") else None,
                        dedupe_key=row[15], delivery_attempts=int(row[16] or 0),
                        last_attempt_at=row[17].isoformat() if hasattr(row[17], "isoformat") else None,
                        delivery_error=row[18], max_attempts=int(row[19] or 3),
                        next_attempt_at=row[20].isoformat() if hasattr(row[20], "isoformat") else None,
                        dead_lettered_at=row[21].isoformat() if hasattr(row[21], "isoformat") else None,
                    )
                    n.delivery_attempts += 1
                    try:
                        result = self.delivery_func(n, email_config=email_config or {})
                    except Exception as exc:
                        error = str(exc)[:4000]
                        if n.delivery_attempts >= n.max_attempts:
                            dead += 1
                            conn.execute(
                                """UPDATE notification_outbox SET delivery_attempts=%s,last_attempt_at=%s,
                                delivery_error=%s,dead_lettered_at=%s,next_attempt_at=NULL
                                WHERE organization_id=%s AND notification_id=%s""",
                                (n.delivery_attempts, now, error, now, organization_id, row[1]),
                            )
                        else:
                            retried += 1
                            next_at = now + timedelta(seconds=backoff_seconds(n.delivery_attempts))
                            conn.execute(
                                """UPDATE notification_outbox SET delivery_attempts=%s,last_attempt_at=%s,
                                delivery_error=%s,next_attempt_at=%s
                                WHERE organization_id=%s AND notification_id=%s""",
                                (n.delivery_attempts, now, error, next_at, organization_id, row[1]),
                            )
                        continue
                    sent += 1
                    conn.execute(
                        """UPDATE notification_outbox SET status='SENT',delivery_attempts=%s,last_attempt_at=%s,
                        sent_by=%s,sent_at=%s,delivery_error=NULL,next_attempt_at=NULL
                        WHERE organization_id=%s AND notification_id=%s""",
                        (n.delivery_attempts, now, actor_id, now, organization_id, row[1]),
                    )
        return NotificationRun(processed, sent, retried, dead)
