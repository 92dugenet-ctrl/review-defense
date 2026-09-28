"""V5.8 Google sync engine.

Turns Google Business Profile review notifications and scheduled reconciliation
into durable, idempotent background jobs. Network access remains behind the V5.7
client; this layer never reports, deletes, or replies to reviews.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping

from .background_jobs import SQLiteJobQueue, JobWorker
from .google_business_profile import GoogleBusinessProfileClient, ReviewCache, ReviewSyncItem


class SyncEventType(str, Enum):
    NEW_REVIEW = "NEW_REVIEW"
    UPDATED_REVIEW = "UPDATED_REVIEW"
    RECONCILE_LOCATION = "RECONCILE_LOCATION"


@dataclass(frozen=True)
class GoogleReviewEvent:
    event_id: str
    event_type: SyncEventType
    account_id: str
    location_id: str
    review_id: str | None
    occurred_at: str | None = None


@dataclass(frozen=True)
class SyncCursor:
    organization_id: str
    account_id: str
    location_id: str
    next_page_token: str | None
    updated_at: float


class SyncStateStore:
    """Durable SQLite state for cursors and event de-duplication."""
    def __init__(self, path: str = ":memory:", *, clock: Callable[[], float] = time.time):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.clock = clock
        self.lock = threading.RLock()
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS sync_cursors (
            organization_id TEXT NOT NULL,
            account_id TEXT NOT NULL,
            location_id TEXT NOT NULL,
            next_page_token TEXT,
            updated_at REAL NOT NULL,
            PRIMARY KEY (organization_id, account_id, location_id)
        );
        CREATE TABLE IF NOT EXISTS processed_events (
            organization_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            processed_at REAL NOT NULL,
            PRIMARY KEY (organization_id, event_id)
        );
        """)
        self.db.commit()

    def get_cursor(self, organization_id: str, account_id: str, location_id: str) -> SyncCursor | None:
        with self.lock:
            row = self.db.execute(
                "SELECT * FROM sync_cursors WHERE organization_id=? AND account_id=? AND location_id=?",
                (organization_id, account_id, location_id),
            ).fetchone()
        if not row:
            return None
        return SyncCursor(row["organization_id"], row["account_id"], row["location_id"], row["next_page_token"], row["updated_at"])

    def put_cursor(self, organization_id: str, account_id: str, location_id: str, next_page_token: str | None) -> SyncCursor:
        now = self.clock()
        with self.lock:
            self.db.execute("""INSERT INTO sync_cursors
                (organization_id, account_id, location_id, next_page_token, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(organization_id, account_id, location_id)
                DO UPDATE SET next_page_token=excluded.next_page_token, updated_at=excluded.updated_at""",
                (organization_id, account_id, location_id, next_page_token, now))
            self.db.commit()
        return SyncCursor(organization_id, account_id, location_id, next_page_token, now)

    def claim_event(self, organization_id: str, event_id: str) -> bool:
        if not organization_id or not event_id:
            raise ValueError("organization_id and event_id are required")
        now = self.clock()
        with self.lock:
            try:
                self.db.execute("INSERT INTO processed_events VALUES (?, ?, ?)", (organization_id, event_id, now))
                self.db.commit()
                return True
            except sqlite3.IntegrityError:
                self.db.rollback()
                return False

    def close(self) -> None:
        with self.lock:
            self.db.close()


class ReviewEventParser:
    """Parses Pub/Sub push envelopes without trusting arbitrary fields."""
    ALLOWED = {"NEW_REVIEW", "UPDATED_REVIEW"}

    @staticmethod
    def parse(payload: Mapping[str, Any]) -> GoogleReviewEvent:
        message = payload.get("message") if isinstance(payload.get("message"), Mapping) else payload
        event_id = str(message.get("messageId") or message.get("message_id") or payload.get("eventId") or "")
        if not event_id:
            raise ValueError("Pub/Sub event id is required")
        attrs = message.get("attributes") if isinstance(message.get("attributes"), Mapping) else {}
        event_type = str(attrs.get("eventType") or attrs.get("notificationType") or payload.get("eventType") or "")
        event_type = event_type.upper()
        if event_type not in ReviewEventParser.ALLOWED:
            raise ValueError("unsupported Google review event type")
        resource = str(attrs.get("resource") or attrs.get("review") or payload.get("resource") or "")
        parts = resource.split("/")
        try:
            ai = parts.index("accounts")
            li = parts.index("locations")
            account_id = parts[ai + 1]
            location_id = parts[li + 1]
            review_id = parts[parts.index("reviews") + 1] if "reviews" in parts else None
        except (ValueError, IndexError):
            raise ValueError("invalid Google review resource")
        if not account_id or not location_id:
            raise ValueError("Google event is missing account/location")
        return GoogleReviewEvent(event_id, SyncEventType(event_type), account_id, location_id, review_id, payload.get("occurredAt"))


class GoogleSyncEngine:
    """Coordinates notification-driven fetches and periodic reconciliation."""
    def __init__(self, *, client_factory: Callable[[str], GoogleBusinessProfileClient], state: SyncStateStore,
                 review_cache: ReviewCache | None = None, queue: SQLiteJobQueue | None = None):
        self.client_factory = client_factory
        self.state = state
        self.review_cache = review_cache or ReviewCache()
        self.queue = queue or SQLiteJobQueue(":memory:")
        self._results: dict[tuple[str, str], list[ReviewSyncItem]] = {}
        self._lock = threading.RLock()

    def enqueue_event(self, organization_id: str, event: GoogleReviewEvent) -> str | None:
        if event.event_id and not self.state.claim_event(organization_id, event.event_id):
            return None
        payload = {"event_id": event.event_id, "event_type": event.event_type.value,
                   "account_id": event.account_id, "location_id": event.location_id,
                   "review_id": event.review_id}
        return self.queue.enqueue(organization_id=organization_id, kind="google.review.event", payload=payload, idempotency_key=event.event_id)

    def enqueue_reconciliation(self, organization_id: str, account_id: str, location_id: str) -> str:
        payload = {"account_id": account_id, "location_id": location_id}
        cursor = self.state.get_cursor(organization_id, account_id, location_id)
        generation = "0" if cursor is None else str(cursor.updated_at)
        # Deduplicate overlapping runs for the same cursor generation, while allowing
        # the next scheduled reconciliation after a cursor update to run again.
        key = f"reconcile:{organization_id}:{account_id}:{location_id}:{generation}"
        job = self.queue.enqueue(organization_id=organization_id, kind="google.review.reconcile", payload=payload, idempotency_key=key)
        return job.id

    def handlers(self) -> Mapping[str, Callable[[Mapping[str, Any]], Any]]:
        return {"google.review.event": self._handle_event, "google.review.reconcile": self._handle_reconcile}

    def worker(self, organization_id: str, worker_id: str = "google-sync") -> JobWorker:
        # The queue itself is tenant-scoped; handlers additionally reject payloads that do not belong to the worker tenant.
        def scoped(kind: str, fn):
            def wrapped(payload):
                fn(organization_id, payload)
            return wrapped
        return JobWorker(self.queue, {
            "google.review.event": scoped("google.review.event", self._handle_event),
            "google.review.reconcile": scoped("google.review.reconcile", self._handle_reconcile),
        }, worker_id=worker_id)

    def _handle_event(self, organization_id: str, payload: Mapping[str, Any]) -> None:
        event = GoogleReviewEvent(str(payload["event_id"]), SyncEventType(str(payload["event_type"])),
                                  str(payload["account_id"]), str(payload["location_id"]),
                                  payload.get("review_id"))
        client = self.client_factory(organization_id)
        if not event.review_id:
            self._reconcile_page(organization_id, client, event.account_id, event.location_id, None)
            return
        review = client.get_review(event.account_id, event.location_id, event.review_id)
        item = self.review_cache.observe(review)
        self._record(organization_id, item)

    def _handle_reconcile(self, organization_id: str, payload: Mapping[str, Any]) -> None:
        client = self.client_factory(organization_id)
        account_id, location_id = str(payload["account_id"]), str(payload["location_id"])
        cursor = self.state.get_cursor(organization_id, account_id, location_id)
        token = cursor.next_page_token if cursor else None
        self._reconcile_page(organization_id, client, account_id, location_id, token)

    def _reconcile_page(self, organization_id: str, client: GoogleBusinessProfileClient, account_id: str,
                        location_id: str, token: str | None) -> None:
        result = client.list_reviews(account_id, location_id, page_token=token, page_size=50)
        for item in result.items:
            self._record(organization_id, self.review_cache.observe(item))
        # Store the server cursor exactly as observed. When exhausted, reset it so a future reconciliation
        # starts from page one; this also mitigates Google's documented occasional later-page inconsistency.
        self.state.put_cursor(organization_id, account_id, location_id, result.next_page_token)

    def _record(self, organization_id: str, item: ReviewSyncItem) -> None:
        with self._lock:
            self._results.setdefault((organization_id, item.review.review_id), []).append(item)

    def results(self, organization_id: str, review_id: str | None = None) -> list[ReviewSyncItem]:
        with self._lock:
            if review_id is not None:
                return list(self._results.get((organization_id, review_id), []))
            return [item for (org, _), items in self._results.items() if org == organization_id for item in items]


def pubsub_push_to_event(payload: Mapping[str, Any]) -> GoogleReviewEvent:
    return ReviewEventParser.parse(payload)
