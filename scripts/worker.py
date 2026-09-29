#!/usr/bin/env python3
"""Production worker entrypoint.

The worker is intentionally tenant-scoped: a deployment must provide
REVIEW_DEFENSE_WORKER_ORGANIZATION_ID. This prevents a background process from
accidentally bypassing tenant boundaries.
"""
from __future__ import annotations

import importlib
import os
import socket

from src.postgres_processing import PostgresProcessingQueue
from src.postgres_notification_worker import PostgresNotificationWorker


def _dsn() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise SystemExit("DATABASE_URL is required")
    return value


def _organization() -> str:
    value = os.getenv("REVIEW_DEFENSE_WORKER_ORGANIZATION_ID", "").strip()
    if not value:
        raise SystemExit("REVIEW_DEFENSE_WORKER_ORGANIZATION_ID is required")
    return value


def run_processing_once() -> None:
    queue = PostgresProcessingQueue(_dsn())
    organization_id = _organization()
    worker_id = os.getenv("REVIEW_DEFENSE_WORKER_ID", socket.gethostname())
    job = queue.claim(organization_id=organization_id, worker_id=worker_id, lease_seconds=60)
    if job is None:
        return
    handlers = {}
    spec = os.getenv("REVIEW_DEFENSE_JOB_HANDLERS", "").strip()
    if spec:
        for item in spec.split(","):
            module_name, function_name = item.split(":", 1)
            handlers[item] = getattr(importlib.import_module(module_name), function_name)
    handler = handlers.get(job.kind)
    if handler is None:
        queue.fail(organization_id, job.job_id, worker_id, f"no handler registered for {job.kind}")
        return
    try:
        handler(job.payload)
    except Exception as exc:
        queue.fail(organization_id, job.job_id, worker_id, f"{type(exc).__name__}: {exc}")
    else:
        queue.complete(organization_id, job.job_id, worker_id)


if __name__ == "__main__":
    run_processing_once()
