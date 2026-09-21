"""V5.6 durable background-job primitives.

A small SQLite-backed queue intended as a framework-neutral reference adapter.
It provides persistent state, priority ordering, idempotency, bounded retries,
lease recovery after worker crashes, and a dead-letter queue. No external
network calls are performed by this module.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping


class JobState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    DEAD_LETTER = "DEAD_LETTER"
    CANCELLED = "CANCELLED"


class JobNotFound(KeyError):
    pass


class JobIdempotencyConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class Job:
    id: str
    organization_id: str
    kind: str
    payload: Mapping[str, Any]
    state: JobState
    priority: int
    attempts: int
    max_attempts: int
    run_after: float
    idempotency_key: str | None
    payload_fingerprint: str
    lease_owner: str | None
    leased_until: float | None
    last_error: str | None
    created_at: float
    updated_at: float


class SQLiteJobQueue:
    """Durable local queue; production can replace the storage adapter with PostgreSQL."""

    def __init__(self, path: str = ":memory:", *, clock: Callable[[], float] = time.time) -> None:
        self.path = path
        self.clock = clock
        self._lock = threading.RLock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                state TEXT NOT NULL,
                priority INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL,
                run_after REAL NOT NULL,
                idempotency_key TEXT,
                payload_fingerprint TEXT NOT NULL,
                lease_owner TEXT,
                leased_until REAL,
                last_error TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(organization_id, idempotency_key)
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_ready
              ON jobs(state, run_after, priority DESC, created_at ASC);
            CREATE INDEX IF NOT EXISTS idx_jobs_lease
              ON jobs(state, leased_until);
            """
        )
        self._db.commit()

    @staticmethod
    def fingerprint(payload: Mapping[str, Any]) -> str:
        import hashlib
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return hashlib.sha256(raw).hexdigest()

    def enqueue(self, *, organization_id: str, kind: str, payload: Mapping[str, Any],
                priority: int = 0, max_attempts: int = 3, run_after: float | None = None,
                idempotency_key: str | None = None) -> Job:
        if not organization_id or not kind:
            raise ValueError("organization_id and kind are required")
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        fp = self.fingerprint(payload)
        now = self.clock()
        with self._lock:
            if idempotency_key is not None:
                existing = self._db.execute(
                    "SELECT * FROM jobs WHERE organization_id=? AND idempotency_key=?",
                    (organization_id, idempotency_key),
                ).fetchone()
                if existing:
                    if existing["payload_fingerprint"] != fp:
                        raise JobIdempotencyConflict("idempotency key reused with different payload")
                    return self._row(existing)
            job_id = str(uuid.uuid4())
            self._db.execute(
                """INSERT INTO jobs
                (id, organization_id, kind, payload, state, priority, attempts,
                 max_attempts, run_after, idempotency_key, payload_fingerprint,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)""",
                (job_id, organization_id, kind, json.dumps(payload, sort_keys=True),
                 JobState.QUEUED.value, int(priority), max_attempts,
                 now if run_after is None else float(run_after), idempotency_key, fp, now, now),
            )
            self._db.commit()
            return self.get(job_id, organization_id=organization_id)

    def _row(self, row: sqlite3.Row) -> Job:
        return Job(
            id=row["id"], organization_id=row["organization_id"], kind=row["kind"],
            payload=json.loads(row["payload"]), state=JobState(row["state"]),
            priority=row["priority"], attempts=row["attempts"], max_attempts=row["max_attempts"],
            run_after=row["run_after"], idempotency_key=row["idempotency_key"],
            payload_fingerprint=row["payload_fingerprint"], lease_owner=row["lease_owner"],
            leased_until=row["leased_until"], last_error=row["last_error"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def get(self, job_id: str, *, organization_id: str | None = None) -> Job:
        with self._lock:
            row = self._db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row or (organization_id is not None and row["organization_id"] != organization_id):
            raise JobNotFound(job_id)
        return self._row(row)

    def recover_expired_leases(self) -> int:
        now = self.clock()
        with self._lock:
            cur = self._db.execute(
                """UPDATE jobs SET state=?, lease_owner=NULL, leased_until=NULL, run_after=?, updated_at=?
                   WHERE state=? AND leased_until IS NOT NULL AND leased_until <= ?""",
                (JobState.RETRY_SCHEDULED.value, now, now, JobState.RUNNING.value, now),
            )
            self._db.commit()
            return cur.rowcount

    def claim(self, *, worker_id: str, lease_seconds: float = 30.0) -> Job | None:
        if not worker_id or lease_seconds <= 0:
            raise ValueError("worker_id and positive lease_seconds are required")
        now = self.clock()
        with self._lock:
            self.recover_expired_leases()
            row = self._db.execute(
                """SELECT * FROM jobs
                   WHERE state IN (?, ?) AND run_after <= ?
                   ORDER BY priority DESC, created_at ASC LIMIT 1""",
                (JobState.QUEUED.value, JobState.RETRY_SCHEDULED.value, now),
            ).fetchone()
            if not row:
                return None
            cur = self._db.execute(
                """UPDATE jobs SET state=?, attempts=attempts+1, lease_owner=?, leased_until=?, updated_at=?
                   WHERE id=? AND state IN (?, ?)""",
                (JobState.RUNNING.value, worker_id, now + lease_seconds, now, row["id"],
                 JobState.QUEUED.value, JobState.RETRY_SCHEDULED.value),
            )
            if cur.rowcount != 1:
                self._db.rollback()
                return None
            self._db.commit()
            return self.get(row["id"])

    def succeed(self, job_id: str, *, worker_id: str) -> Job:
        return self._finish(job_id, worker_id=worker_id, state=JobState.SUCCEEDED)

    def fail(self, job_id: str, *, worker_id: str, error: str, retry_delay: float = 1.0) -> Job:
        if retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
        now = self.clock()
        with self._lock:
            row = self._db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                raise JobNotFound(job_id)
            self._assert_owner(row, worker_id)
            terminal = row["attempts"] >= row["max_attempts"]
            state = JobState.DEAD_LETTER if terminal else JobState.RETRY_SCHEDULED
            run_after = now if terminal else now + retry_delay
            self._db.execute(
                """UPDATE jobs SET state=?, run_after=?, lease_owner=NULL, leased_until=NULL,
                   last_error=?, updated_at=? WHERE id=?""",
                (state.value, run_after, str(error)[:2000], now, job_id),
            )
            self._db.commit()
            return self.get(job_id)

    def cancel(self, job_id: str, *, organization_id: str) -> Job:
        now = self.clock()
        with self._lock:
            row = self._db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row or row["organization_id"] != organization_id:
                raise JobNotFound(job_id)
            if row["state"] == JobState.RUNNING.value:
                raise RuntimeError("running jobs cannot be cancelled by this primitive")
            self._db.execute("UPDATE jobs SET state=?, updated_at=? WHERE id=?", (JobState.CANCELLED.value, now, job_id))
            self._db.commit()
            return self.get(job_id, organization_id=organization_id)

    def _assert_owner(self, row: sqlite3.Row, worker_id: str) -> None:
        if row["state"] != JobState.RUNNING.value or row["lease_owner"] != worker_id:
            raise RuntimeError("job lease is not owned by worker")

    def _finish(self, job_id: str, *, worker_id: str, state: JobState) -> Job:
        now = self.clock()
        with self._lock:
            row = self._db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                raise JobNotFound(job_id)
            self._assert_owner(row, worker_id)
            self._db.execute(
                "UPDATE jobs SET state=?, lease_owner=NULL, leased_until=NULL, updated_at=? WHERE id=?",
                (state.value, now, job_id),
            )
            self._db.commit()
            return self.get(job_id)

    def dead_letters(self, *, organization_id: str | None = None) -> list[Job]:
        with self._lock:
            if organization_id is None:
                rows = self._db.execute("SELECT * FROM jobs WHERE state=? ORDER BY updated_at", (JobState.DEAD_LETTER.value,)).fetchall()
            else:
                rows = self._db.execute("SELECT * FROM jobs WHERE state=? AND organization_id=? ORDER BY updated_at", (JobState.DEAD_LETTER.value, organization_id)).fetchall()
        return [self._row(r) for r in rows]

    def close(self) -> None:
        with self._lock:
            self._db.close()


class JobWorker:
    """Synchronous worker loop suitable for one process or as a test harness."""
    def __init__(self, queue: SQLiteJobQueue, handlers: Mapping[str, Callable[[Mapping[str, Any]], Any]], *, worker_id: str,
                 lease_seconds: float = 30.0, retry_delay: float = 1.0) -> None:
        self.queue = queue
        self.handlers = dict(handlers)
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds
        self.retry_delay = retry_delay

    def run_once(self) -> Job | None:
        job = self.queue.claim(worker_id=self.worker_id, lease_seconds=self.lease_seconds)
        if job is None:
            return None
        handler = self.handlers.get(job.kind)
        if handler is None:
            return self.queue.fail(job.id, worker_id=self.worker_id, error=f"no handler for {job.kind}", retry_delay=self.retry_delay)
        try:
            handler(job.payload)
        except Exception as exc:
            return self.queue.fail(job.id, worker_id=self.worker_id, error=f"{type(exc).__name__}: {exc}", retry_delay=self.retry_delay)
        return self.queue.succeed(job.id, worker_id=self.worker_id)
