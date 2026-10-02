"""V6.15 notification delivery observability.

Read-only, tenant-scoped operational metrics. This module never performs I/O or
changes notification state; it derives metrics from the notification records and
already-audited lifecycle events.
"""
from __future__ import annotations
from collections import Counter
from typing import Iterable, Mapping, Any


def build_notification_metrics(notifications: Iterable[Any], audit_events: Iterable[Mapping[str, Any]], *, organization_id: str) -> dict[str, Any]:
    if not organization_id:
        raise ValueError("organization_id is required")
    rows = [n for n in notifications if getattr(n, "organization_id", None) == organization_id]
    audits = [a for a in audit_events if a.get("organization_id") == organization_id]
    statuses = Counter(getattr(n, "status", "UNKNOWN") for n in rows)
    channels = Counter(getattr(n, "channel", "UNKNOWN") for n in rows)
    levels = Counter(getattr(n, "escalation_level", "UNKNOWN") for n in rows)
    attempts = sum(int(getattr(n, "delivery_attempts", 0) or 0) for n in rows)
    dead = sum(1 for n in rows if getattr(n, "dead_lettered_at", None))
    failed = sum(1 for a in audits if a.get("action") == "ESCALATION_NOTIFICATION_DELIVERY_FAILED")
    delivered = sum(1 for a in audits if a.get("action") == "ESCALATION_NOTIFICATION_DELIVERED")
    queued = sum(1 for a in audits if a.get("action") == "ESCALATION_NOTIFICATION_QUEUED")
    blocked = sum(1 for a in audits if a.get("action") == "ESCALATION_NOTIFICATION_BLOCKED")
    worker_runs = sum(1 for a in audits if a.get("action") == "NOTIFICATION_WORKER_RUN")
    retries = sum(1 for a in audits if a.get("action") == "ESCALATION_NOTIFICATION_RETRY_SCHEDULED")
    return {
        "organization_id": organization_id,
        "notifications": {"total": len(rows), "by_status": dict(sorted(statuses.items())), "by_channel": dict(sorted(channels.items())), "by_level": dict(sorted(levels.items()))},
        "delivery": {"attempts": attempts, "delivered_events": delivered, "failed_events": failed, "retry_events": retries, "dead_lettered": dead},
        "workflow": {"queued_events": queued, "policy_blocked_events": blocked, "worker_runs": worker_runs},
    }
