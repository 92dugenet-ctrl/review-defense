"""V5.1 PostgreSQL persistence boundary.
Requires psycopg (v3) in a deployed environment; imports are deferred.
"""
from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator

class RepositoryError(RuntimeError): pass

class PostgresRepository:
    def __init__(self, dsn: str, connect_factory=None):
        self.dsn = dsn
        self._connect_factory = connect_factory

    def _connect(self):
        if self._connect_factory:
            return self._connect_factory(self.dsn)
        try:
            import psycopg
        except ImportError as exc:
            raise RepositoryError("psycopg is required for PostgreSQL persistence") from exc
        return psycopg.connect(self.dsn)

    @contextmanager
    def transaction(self, organization_id: str) -> Iterator[object]:
        if not organization_id:
            raise ValueError("organization_id is required")
        conn = self._connect()
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT set_config('app.organization_id', %s, true)",
                        (organization_id,),
                    )
                    yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction_without_tenant(self) -> Iterator[object]:
        """Open a transaction without setting tenant context.

        This is reserved for security-boundary lookups whose only credential
        is the opaque token itself, such as restoring a persisted session
        before the organization is known. Tenant-scoped operations must keep
        using transaction(organization_id).
        """
        conn = self._connect()
        try:
            with conn.transaction():
                yield conn
        finally:
            conn.close()

    def create_privacy_request(self, organization_id: str, requester_user_id: str, request_type: str, details: dict, due_at: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO privacy_requests
                      (organization_id, requester_user_id, request_type, details, due_at)
                    VALUES (%s,%s,%s,%s::jsonb,%s)
                    RETURNING id, status, created_at, updated_at, due_at
                """, (organization_id, requester_user_id, request_type, __import__("json").dumps(details), due_at))
                return cur.fetchone()

    def list_privacy_requests(self, organization_id: str, requester_user_id: str | None = None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                if requester_user_id:
                    cur.execute("""
                        SELECT id, organization_id, requester_user_id, request_type, status,
                               details, response_note, due_at, created_at, updated_at
                        FROM privacy_requests
                        WHERE requester_user_id=%s
                        ORDER BY created_at DESC
                    """, (requester_user_id,))
                else:
                    cur.execute("""
                        SELECT id, organization_id, requester_user_id, request_type, status,
                               details, response_note, due_at, created_at, updated_at
                        FROM privacy_requests
                        ORDER BY created_at DESC
                    """)
                return cur.fetchall()

    def update_privacy_request(self, organization_id: str, request_id: str, status: str, response_note: str | None = None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE privacy_requests
                    SET status=%s, response_note=%s, updated_at=now()
                    WHERE id=%s
                    RETURNING id, status, response_note, due_at, created_at, updated_at
                """, (status, response_note, request_id))
                return cur.fetchone()

    def create_privacy_consent(self, organization_id: str, user_id: str, purpose: str, policy_version: str, granted: bool):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO privacy_consents
                      (organization_id, user_id, purpose, policy_version, granted, withdrawn_at)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    RETURNING id, purpose, policy_version, granted, granted_at, withdrawn_at
                """, (organization_id, user_id, purpose, policy_version, bool(granted),
                      None if granted else __import__("datetime").datetime.now(__import__("datetime").timezone.utc)))
                return cur.fetchone()

    def list_privacy_consents(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, purpose, policy_version, granted, granted_at, withdrawn_at
                    FROM privacy_consents
                    WHERE user_id=%s
                    ORDER BY granted_at DESC
                """, (user_id,))
                return cur.fetchall()

    def ping(self) -> bool:
        """Check database connectivity without requiring tenant context."""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
        finally:
            conn.close()

    def create_case(self, organization_id: str, review_id: str, state: str, actor_user_id: str | None = None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO cases (organization_id, review_id, state)
                    VALUES (%s,%s,%s)
                    RETURNING id, organization_id, review_id, state, created_at, updated_at
                """, (organization_id, review_id, state))
                case = cur.fetchone()
                cur.execute("""
                    INSERT INTO case_events (organization_id, case_id, event_type, actor_user_id, payload)
                    VALUES (%s,%s,%s,%s,%s::jsonb)
                """, (organization_id, case[0], "CASE_CREATED", actor_user_id, '{}'))
                return case

    def list_case_review_checklist(self, organization_id: str, case_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT item_id, organization_id, case_id, code, label, required, completed, completed_by, completed_at, note FROM case_review_checklist WHERE case_id=%s ORDER BY code", (case_id,))
                return cur.fetchall()

    def upsert_case_review_checklist(self, organization_id: str, item: dict):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO case_review_checklist (item_id, organization_id, case_id, code, label, required, completed, completed_by, completed_at, note)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (organization_id, case_id, code) DO UPDATE SET
                      label=EXCLUDED.label, required=EXCLUDED.required, completed=EXCLUDED.completed,
                      completed_by=EXCLUDED.completed_by, completed_at=EXCLUDED.completed_at, note=EXCLUDED.note
                """, (item["item_id"], organization_id, item["case_id"], item["code"], item["label"], item["required"], item["completed"], item["completed_by"], item["completed_at"], item["note"]))

    def get_case(self, organization_id: str, case_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, organization_id, review_id, state, created_at, updated_at FROM cases WHERE id=%s", (case_id,))
                return cur.fetchone()
