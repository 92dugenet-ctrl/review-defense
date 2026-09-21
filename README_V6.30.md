# Review Defense V6.30 — Backup/Restore & Disaster Recovery Validation

V6.30 adds a deterministic disaster-recovery validation harness around the existing PostgreSQL backup/restore tooling.

## What is implemented

- `scripts/dr_validate.py` validates a complete isolated DR cycle.
- Live source database is accepted **only** from `REVIEW_DEFENSE_TEST_DATABASE_URL`.
- `DATABASE_URL` is never used as a fallback.
- Production-looking source/target databases are rejected.
- Restore target must be explicit, different from source, and protected by `--confirm`.
- PostgreSQL custom-format backup is created with `pg_dump`.
- Backup size and SHA-256 are recorded.
- Restore uses `pg_restore --clean --if-exists --no-owner`.
- Restored schema/migrations, tenant records, case records, evidence SHA-256, membership, and tenant RLS isolation are checked.
- A machine-readable JSON report is emitted.
- No external Google action, review deletion/reporting, or automatic remediation is introduced.

## Live run

The live DR check requires two dedicated non-production PostgreSQL databases and PostgreSQL client binaries:

```bash
REVIEW_DEFENSE_TEST_DATABASE_URL='postgresql://...' \
python scripts/dr_validate.py \
  --restore-database-url 'postgresql://...' \
  --confirm \
  --backup artifacts/v6.30-dr.backup.dump \
  --output artifacts/v6.30-dr-report.json
```

The current execution environment does not provide a live PostgreSQL server, so the release validation below covers the deterministic/contract layer; the real DB cycle must be run against dedicated staging databases.

## Recovery procedure

1. Stop application writes or place the application in maintenance mode.
2. Preserve the backup file and its SHA-256 in the incident record.
3. Restore into a separate staging database first.
4. Run migrations/schema checks and tenant-isolation validation.
5. Validate evidence hashes and critical audit records.
6. Obtain human operational approval before changing the production database target.
7. Restore production only through the separately controlled operational procedure.
8. Record the restore timestamp, backup SHA-256, operator, target, and validation report.

V6.30 intentionally does not automate production restoration.
