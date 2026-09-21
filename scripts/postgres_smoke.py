#!/usr/bin/env python3
"""Run the V6.23 live PostgreSQL smoke test against an explicitly named test DB.

Usage:
  REVIEW_DEFENSE_TEST_DATABASE_URL=postgresql://... python scripts/postgres_smoke.py

The script refuses to use DATABASE_URL so it cannot accidentally mutate production.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.migration_runner import apply_migrations  # noqa: E402
from src.postgres_integration import IntegrationConfig, connect, wait_for_database  # noqa: E402
from src.postgres_repository import PostgresRepository  # noqa: E402


def main() -> int:
    if not os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL"):
        print("ERROR: REVIEW_DEFENSE_TEST_DATABASE_URL is required; refusing DATABASE_URL fallback.", file=sys.stderr)
        return 2
    cfg = IntegrationConfig.from_env()
    wait_for_database(cfg)

    class ConnAdapter:
        def __call__(self, _dsn):
            return connect(cfg)

    applied = apply_migrations(lambda: connect(cfg), ROOT / "migrations")
    print(f"migrations: applied={len(applied)}")

    repo = PostgresRepository(cfg.dsn, connect_factory=ConnAdapter())
    org_a = str(uuid.uuid4())
    org_b = str(uuid.uuid4())
    case_a = None
    try:
        # Seed tenants outside RLS using a dedicated test connection before setting tenant context.
        conn = connect(cfg)
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO organizations(id,name) VALUES(%s,%s)", (org_a, "V623 smoke A"))
                    cur.execute("INSERT INTO organizations(id,name) VALUES(%s,%s)", (org_b, "V623 smoke B"))
        finally:
            conn.close()

        row = repo.create_case(org_a, "v623-smoke", "OPEN")
        case_a = str(row[0])
        assert repo.get_case(org_a, case_a)[0] == row[0]
        assert repo.get_case(org_b, case_a) is None, "tenant isolation failed"

        # Verify rollback: a failed transaction must not persist a partial event.
        conn = connect(cfg)
        try:
            try:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute("SET LOCAL app.organization_id = %s", (org_a,))
                        cur.execute("INSERT INTO case_events(organization_id,case_id,event_type) VALUES(%s,%s,%s)", (org_a, case_a, "V623_ROLLBACK"))
                        cur.execute("SELECT 1/0")
            except Exception:
                pass
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL app.organization_id = %s", (org_a,))
                    cur.execute("SELECT count(*) FROM case_events WHERE organization_id=%s AND case_id=%s AND event_type='V623_ROLLBACK'", (org_a, case_a))
                    assert cur.fetchone()[0] == 0
        finally:
            conn.close()

        print("postgres smoke: PASS")
        return 0
    finally:
        conn = connect(cfg)
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM organizations WHERE id IN (%s,%s)", (org_a, org_b))
        finally:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
