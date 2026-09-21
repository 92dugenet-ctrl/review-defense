# Review Defense V6.22 — PostgreSQL Production Integration & Data Reliability

V6.22 hardens the persistence layer for production deployment without adding autonomous external actions.

## Added
- Migration checksums in `schema_migrations` to detect post-application migration drift.
- Transaction-scoped PostgreSQL advisory lock around migrations to prevent concurrent migration races.
- Tenant-owned tables are forced through PostgreSQL RLS and receive both `USING` and `WITH CHECK` policies.
- Production indexes for session expiry, security audit queries, evidence, case events and idempotency records.
- Automatic `updated_at` triggers for core case tables.
- Backfill of `api_sessions.last_seen_at` for legacy sessions.
- Regression tests for migration integrity and V6.22 SQL controls.

## Validation
The suite must pass in full before release packaging. A live PostgreSQL integration environment is still required for final release-candidate validation; this environment does not include Docker in the current execution sandbox.

## Security invariants
- Tenant isolation remains enforced server-side by RLS.
- Existing human approval gates remain unchanged.
- No Google review mutation is performed automatically.
- Migration drift is rejected rather than silently accepted.
