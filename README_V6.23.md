# Review Defense V6.23 — PostgreSQL Integration & Recovery Readiness

V6.23 turns the PostgreSQL production foundation into an explicit, reproducible integration workflow.

## Added
- Live PostgreSQL integration helpers using `REVIEW_DEFENSE_TEST_DATABASE_URL` only.
- A smoke test that applies migrations, verifies tenant isolation and verifies transaction rollback.
- `scripts/postgres_smoke.py` for operator-run integration validation.
- `scripts/postgres_backup.py` for custom-format `pg_dump` backups.
- `scripts/postgres_restore.py` for explicit, confirmed `pg_restore` recovery.
- Restore tooling never falls back to `DATABASE_URL`, preventing accidental destructive restores.
- Integration tests are opt-in and never silently target production.

## Validation
- The standard regression suite must pass before packaging.
- Live PostgreSQL smoke validation requires a PostgreSQL server and psycopg; it is intentionally separate from the default unit suite.
- A backup/restore drill must be executed against a disposable PostgreSQL database before Release Candidate.

## Security invariants
- Tenant isolation remains server-side with PostgreSQL RLS.
- No automatic Google review mutation is introduced.
- Restore is destructive only after explicit `--confirm` and explicit target DSN.
- Production `DATABASE_URL` is never used as the integration-test fallback.
