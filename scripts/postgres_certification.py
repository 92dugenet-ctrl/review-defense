#!/usr/bin/env python3
"""V6.36 real PostgreSQL staging certification.

Requires REVIEW_DEFENSE_TEST_DATABASE_URL and never falls back to DATABASE_URL.
The check is safe to run repeatedly: migrations are applied, re-applied for
idempotency, then critical schema/RLS contracts are inspected.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.migration_runner import apply_migrations  # noqa: E402
from src.postgres_integration import IntegrationConfig, connect, wait_for_database  # noqa: E402

VERSION = "6.36"
REQUIRED_TABLES = {
    "organizations", "users", "memberships", "cases", "case_events",
    "api_sessions", "api_reviews", "api_cases", "api_decisions", "api_approvals",
    "api_submissions", "api_evidence", "evidence_facts", "contradiction_findings",
    "contradiction_dispositions", "contradiction_disposition_history",
    "organization_runtime_settings", "organization_notification_policies",
    "case_escalations", "notification_outbox", "security_events",
    "password_recovery_tokens", "email_verification_tokens", "schema_migrations",
}
RLS_TABLES = {"memberships", "cases", "case_events", "api_sessions", "api_reviews", "api_cases", "api_decisions", "api_approvals", "api_submissions", "api_evidence", "security_events"}

def main() -> int:
    dsn = os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL", "").strip()
    if not dsn:
        print("ERROR: REVIEW_DEFENSE_TEST_DATABASE_URL is required; refusing DATABASE_URL fallback", file=sys.stderr)
        return 2
    if dsn == os.getenv("DATABASE_URL", "") and os.getenv("DATABASE_URL"):
        print("ERROR: test database URL must not equal DATABASE_URL", file=sys.stderr)
        return 2
    cfg = IntegrationConfig.from_env()
    wait_for_database(cfg, attempts=20, delay_seconds=1)
    first = apply_migrations(lambda: connect(cfg), ROOT / "migrations")
    second = apply_migrations(lambda: connect(cfg), ROOT / "migrations")
    conn = connect(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM schema_migrations")
            migration_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM schema_migrations WHERE checksum IS NOT NULL AND length(checksum)=64")
            checksum_count = cur.fetchone()[0]
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = {r[0] for r in cur.fetchall()}
            cur.execute("SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relkind='r' AND relnamespace='public'::regnamespace")
            rls = {r[0]: (bool(r[1]), bool(r[2])) for r in cur.fetchall()}
    finally:
        conn.close()
    missing = sorted(REQUIRED_TABLES - tables)
    missing_rls = sorted(t for t in RLS_TABLES if t not in rls or not rls[t][0] or not rls[t][1])
    result = {
        "version": VERSION,
        "status": "PASS" if not second and not missing and migration_count == len(list((ROOT/'migrations').glob('*.sql'))) and checksum_count == migration_count and not missing_rls else "FAIL",
        "first_apply_count": len(first),
        "second_apply_count": len(second),
        "migration_count": migration_count,
        "checksum_count": checksum_count,
        "required_migrations": len(list((ROOT/'migrations').glob('*.sql'))),
        "missing_tables": missing,
        "missing_forced_rls": missing_rls,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
