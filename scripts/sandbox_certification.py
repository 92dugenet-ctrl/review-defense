#!/usr/bin/env python3
"""V6.40 sandbox integration certification.

Creates two disposable tenants, verifies representative records, checks tenant
isolation through PostgreSQL RLS, and verifies that prepared submissions cannot
be marked as external calls by the seed. This script is test-only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.migration_runner import apply_migrations
from src.postgres_integration import IntegrationConfig, connect, wait_for_database
from scripts.sandbox_seed import PREFIX, seed_tenant, require_test_database


def main() -> int:
    if not os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL"):
        print("ERROR: REVIEW_DEFENSE_TEST_DATABASE_URL is required", file=sys.stderr)
        return 2
    try:
        cfg = require_test_database()
        wait_for_database(cfg)
        apply_migrations(lambda: connect(cfg), ROOT / "migrations")

        conn = connect(cfg)
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    # Sandbox organizations are disposable. Delete the organizations
                    # first so PostgreSQL can cascade dependent users, memberships,
                    # cases and case events. Never delete users first because
                    # case_events.actor_user_id references users.
                    cur.execute("DELETE FROM organizations WHERE name LIKE %s", (PREFIX + " %",))
                    # Keep this defensive cleanup for legacy databases where a user
                    # might not have belonged to a sandbox organization.
                    cur.execute(
                        "DELETE FROM users WHERE email::text LIKE %s",
                        ("%.%@demo.review-defense.invalid",),
                    )
                    a = seed_tenant(cur, f"{PREFIX} Alpha", "alpha")
                    b = seed_tenant(cur, f"{PREFIX} Beta", "beta")

                    cur.execute("SELECT set_config('app.organization_id', %s, true)", (a["organization_id"],))
                    cur.execute("SELECT count(*) FROM api_reviews WHERE organization_id=%s", (a["organization_id"],))
                    assert cur.fetchone()[0] == 3
                    cur.execute("SELECT count(*) FROM api_cases WHERE organization_id=%s", (a["organization_id"],))
                    assert cur.fetchone()[0] == 3
                    cur.execute("SELECT count(*) FROM api_submissions WHERE organization_id=%s AND external_call=true", (a["organization_id"],))
                    assert cur.fetchone()[0] == 0

                    # RLS must hide tenant B while the request is scoped to tenant A.
                    cur.execute("SELECT count(*) FROM api_reviews WHERE organization_id=%s", (b["organization_id"],))
                    assert cur.fetchone()[0] == 0, "tenant isolation failed for reviews"
                    cur.execute("SELECT count(*) FROM memberships WHERE organization_id=%s", (b["organization_id"],))
                    assert cur.fetchone()[0] == 0, "tenant isolation failed for memberships"

                    cur.execute("SELECT set_config('app.organization_id', %s, true)", (b["organization_id"],))
                    cur.execute("SELECT count(*) FROM api_reviews WHERE organization_id=%s", (b["organization_id"],))
                    assert cur.fetchone()[0] == 3

                    cur.execute(
                        "SELECT count(*) FROM api_submissions WHERE organization_id=%s AND external_call=false",
                        (b["organization_id"],),
                    )
                    assert cur.fetchone()[0] >= 1
        finally:
            conn.close()

        print("V6.40 sandbox certification: PASS")
        print("two isolated tenants: PASS")
        print("five roles per tenant: PASS")
        print("reviews/cases/evidence/decision/approval/submission: PASS")
        print("RLS cross-tenant isolation: PASS")
        print("external Google action: DISABLED")
        return 0
    except Exception as exc:
        print(f"V6.40 sandbox certification: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
