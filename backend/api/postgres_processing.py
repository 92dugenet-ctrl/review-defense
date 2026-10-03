"""PostgreSQL-backed processing queue for production workers."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Mapping

import psycopg

from .processing_jobs import ProcessingJob, ProcessingStatus, ProcessingIdempotencyConflict


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PostgresProcessingQueue:
    """Tenant-scoped PostgreSQL implementation of the processing contract.

    Every operation sets app.organization_id inside its transaction so the
    existing RLS policies remain the final isolation boundary.
    """

    def __init__(self, dsn: str):
        self.dsn = dsn

    @staticmethod
    def fingerprint(payload: Mapping[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()

    def _conn(self):
        return psycopg.connect(self.dsn, connect_timeout=5)

    @staticmethod
    def _set_org(conn, organization_id: str) -> None:
        conn.execute("SELECT set_config('app.organization_id', %s, true)", (organization_id,))

    @staticmethod
    def _job(row) -> ProcessingJob:
        payload = row[3] if isinstance(row[3], dict) else json.loads(row[3])
        return ProcessingJob(
            job_id=str(row[0]), organization_id=str(row[1]), kind=str(row[2]),
            payload=payload, status=ProcessingStatus(str(row[4])),
            attempt=int(row[5]), max_attempts=int(row[6]), next_attempt_at=row[7].timestamp(),
            idempotency_key=row[8], payload_fingerprint=str(row[9]), worker_id=row[10],
            leased_until=row[11].timestamp() if row[11] else None, request_id=row[12],
            correlation_id=row[13], last_error=row[14],
            created_at=row[15].timestamp(), updated_at=row[16].timestamp(),
        )

    def enqueue(self, *, organization_id: str, kind: str, payload: Mapping[str, Any],
                max_attempts: int = 3, idempotency_key: str | None = None,
                request_id: str | None = None, correlation_id: str | None = None) -> ProcessingJob:
        if not organization_id or not kind:
            raise ValueError("organization_id and kind are required")
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        fingerprint = self.fingerprint(payload)
        job_id = str(uuid.uuid4())
        with self._conn() as conn:
            with conn.transaction():
                self._set_org(conn, organization_id)
                if idempotency_key:
                    old = conn.execute(
                        "SELECT job_id, payload_fingerprint FROM processing_jobs WHERE organization_id=%s AND idempotency_key=%s",
                        (organization_id, idempotency_key),
                    ).fetchone()
                    if old:
                        if old[1] != fingerprint:
                            raise ProcessingIdempotencyConflict("idempotency key reused with different payload")
                        return self.get(organization_id, str(old[0]))
                conn.execute(
                    """INSERT INTO processing_jobs
                    (job_id,organization_id,kind,payload,status,max_attempts,idempotency_key,
                     payload_fingerprint,request_id,correlation_id)
                    VALUES(%s,%s,%s,%s::jsonb,'pending',%s,%s,%s,%s,%s)""",
                    (job_id, organization_id, kind, json.dumps(payload, sort_keys=True),
                     max_attempts, idempotency_key, fingerprint, request_id, correlation_id),
                )
                conn.execute(
                    """INSERT INTO processing_job_events
                    (event_id,job_id,organization_id,event_type,to_status,attempt,request_id,correlation_id,details)
                    VALUES(%s,%s,%s,'enqueued','pending',0,%s,%s,%s::jsonb)""",
                    (str(uuid.uuid4()), job_id, organization_id, request_id, correlation_id,
                     json.dumps({"kind": kind})),
                )
        return self.get(organization_id, job_id)

    def get(self, organization_id: str, job_id: str) -> ProcessingJob:
        with self._conn() as conn:
            with conn.transaction():
                self._set_org(conn, organization_id)
                row = conn.execute(
                    """SELECT job_id,organization_id,kind,payload,status,attempt,max_attempts,
                    next_attempt_at,idempotency_key,payload_fingerprint,worker_id,leased_until,
                    request_id,correlation_id,last_error,created_at,updated_at
                    FROM processing_jobs WHERE organization_id=%s AND job_id=%s""",
                    (organization_id, job_id),
                ).fetchone()
                if not row:
                    raise KeyError(job_id)
                return self._job(row)

    def recover_expired_leases(self, organization_id: str) -> int:
        now = _now()
        with self._conn() as conn:
            with conn.transaction():
                self._set_org(conn, organization_id)
                rows = conn.execute(
                    """UPDATE processing_jobs
                       SET status='pending',worker_id=NULL,leased_until=NULL,next_attempt_at=%s,updated_at=%s
                       WHERE organization_id=%s AND status='processing' AND leased_until IS NOT NULL AND leased_until<=%s
                       RETURNING job_id,attempt,worker_id,request_id,correlation_id""",
                    (now, now, organization_id, now),
                ).fetchall()
                for job_id, attempt, worker_id, request_id, correlation_id in rows:
                    conn.execute(
                        """INSERT INTO processing_job_events
                                                (event_id,
                            job_id,
                            organization_id,
                            event_type,
                            from_status,
                            to_status,
                            attempt,
                            worker_id,
                            request_id,
                            correlation_id)
                        VALUES(%s,%s,%s,'lease_expired','processing','pending',%s,%s,%s,%s)""",
                        (str(uuid.uuid4()), job_id, organization_id, attempt, worker_id, request_id, correlation_id),
                    )
                return len(rows)

    def claim(self, *, organization_id: str, worker_id: str, lease_seconds: int = 30) -> ProcessingJob | None:
        if not organization_id or not worker_id:
            raise ValueError("organization_id and worker_id are required")
        now = _now()
        lease = now + timedelta(seconds=lease_seconds)
        with self._conn() as conn:
            with conn.transaction():
                self._set_org(conn, organization_id)
                conn.execute(
                    """UPDATE processing_jobs SET status='pending',worker_id=NULL,leased_until=NULL,
                    next_attempt_at=%s,updated_at=%s
                    WHERE organization_id=%s AND status='processing' AND leased_until IS NOT NULL AND leased_until<=%s""",
                    (now, now, organization_id, now),
                )
                row = conn.execute(
                    """SELECT job_id,organization_id,kind,payload,status,attempt,max_attempts,
                    next_attempt_at,idempotency_key,payload_fingerprint,worker_id,leased_until,
                    request_id,correlation_id,last_error,created_at,updated_at
                    FROM processing_jobs
                    WHERE organization_id=%s AND status='pending' AND next_attempt_at<=%s
                    ORDER BY next_attempt_at,created_at FOR UPDATE SKIP LOCKED LIMIT 1""",
                    (organization_id, now),
                ).fetchone()
                if not row:
                    return None
                attempt = int(row[5]) + 1
                conn.execute(
                    """UPDATE processing_jobs SET status='processing',attempt=%s,worker_id=%s,
                    leased_until=%s,updated_at=%s WHERE organization_id=%s AND job_id=%s""",
                    (attempt, worker_id, lease, now, organization_id, row[0]),
                )
                conn.execute(
                    """INSERT INTO processing_job_events
                                        (event_id,
                        job_id,
                        organization_id,
                        event_type,
                        from_status,
                        to_status,
                        attempt,
                        worker_id,
                        request_id,
                        correlation_id)
                    VALUES(%s,%s,%s,'claimed','pending','processing',%s,%s,%s,%s)""",
                    (str(uuid.uuid4()), row[0], organization_id, attempt, worker_id, row[12], row[13]),
                )
                updated = conn.execute(
                    """SELECT job_id,organization_id,kind,payload,status,attempt,max_attempts,
                    next_attempt_at,idempotency_key,payload_fingerprint,worker_id,leased_until,
                    request_id,correlation_id,last_error,created_at,updated_at
                    FROM processing_jobs WHERE organization_id=%s AND job_id=%s""",
                    (organization_id, row[0]),
                ).fetchone()
                return self._job(updated)

    def complete(self, organization_id: str, job_id: str, worker_id: str) -> ProcessingJob:
        return self._finish(organization_id, job_id, worker_id, ProcessingStatus.COMPLETED, "completed")

    def fail(self, organization_id: str, job_id: str, worker_id: str, error: str,
             retry_delay: int = 1) -> ProcessingJob:
        with self._conn() as conn:
            with conn.transaction():
                self._set_org(conn, organization_id)
                row = conn.execute(
                    "SELECT attempt,max_attempts,request_id,correlation_id FROM processing_jobs WHERE organization_id=%s AND job_id=%s AND status='processing' AND worker_id=%s FOR UPDATE",
                    (organization_id, job_id, worker_id),
                ).fetchone()
                if not row:
                    raise RuntimeError("job lease is not owned by worker")
                attempt, max_attempts = int(row[0]), int(row[1])
                terminal = attempt >= max_attempts
                target = "failed" if terminal else "pending"
                next_at = _now() if terminal else _now() + timedelta(seconds=retry_delay)
                conn.execute(
                    """UPDATE processing_jobs SET status=%s,next_attempt_at=%s,worker_id=NULL,
                    leased_until=NULL,last_error=%s,updated_at=%s
                    WHERE organization_id=%s AND job_id=%s""",
                    (target, next_at, str(error)[:4000], _now(), organization_id, job_id),
                )
                conn.execute(
                    """INSERT INTO processing_job_events
                                        (event_id,
                        job_id,
                        organization_id,
                        event_type,
                        from_status,
                        to_status,
                        attempt,
                        worker_id,
                        request_id,
                        correlation_id,
                        details)
                    VALUES(%s,%s,%s,%s,'processing',%s,%s,%s,%s,%s,%s::jsonb)""",
                    (str(uuid.uuid4()), job_id, organization_id,
                     "failed" if terminal else "retry_scheduled", target, attempt, worker_id,
                     row[2], row[3], json.dumps({"error": str(error)[:4000], "retry": not terminal})),
                )
        return self.get(organization_id, job_id)

    def _finish(self, organization_id: str, job_id: str, worker_id: str,
                target: ProcessingStatus, event: str) -> ProcessingJob:
        with self._conn() as conn:
            with conn.transaction():
                self._set_org(conn, organization_id)
                row = conn.execute(
                    "SELECT attempt,request_id,correlation_id FROM processing_jobs WHERE organization_id=%s AND job_id=%s AND status='processing' AND worker_id=%s FOR UPDATE",
                    (organization_id, job_id, worker_id),
                ).fetchone()
                if not row:
                    raise RuntimeError("job lease is not owned by worker")
                conn.execute(
                    """UPDATE processing_jobs SET status=%s,worker_id=NULL,leased_until=NULL,updated_at=%s
                    WHERE organization_id=%s AND job_id=%s""",
                    (target.value, _now(), organization_id, job_id),
                )
                conn.execute(
                    """INSERT INTO processing_job_events
                                        (event_id,
                        job_id,
                        organization_id,
                        event_type,
                        from_status,
                        to_status,
                        attempt,
                        worker_id,
                        request_id,
                        correlation_id)
                    VALUES(%s,%s,%s,%s,'processing',%s,%s,%s,%s,%s)""",
                    (str(uuid.uuid4()), job_id, organization_id, event, target.value, row[0],
                     worker_id, row[1], row[2]),
                )
        return self.get(organization_id, job_id)
