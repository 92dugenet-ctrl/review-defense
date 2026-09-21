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
