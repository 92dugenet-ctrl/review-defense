# Review Defense — V6.35

## Real PostgreSQL CI and migration certification

V6.35 makes the staging validation path exercise a real PostgreSQL 16 service in GitHub Actions instead of relying only on static contracts.

### Added

- GitHub Actions PostgreSQL 16 service container.
- Explicit `REVIEW_DEFENSE_TEST_DATABASE_URL` test database only; no `DATABASE_URL` fallback.
- Migration application against real PostgreSQL.
- Second migration pass to prove idempotency.
- Migration checksum verification.
- Required schema/table verification.
- Forced RLS verification for critical tenant-scoped tables.
- Existing PostgreSQL smoke test executed against the real CI database.
- Regression tests for the certification contract.

### Safety

The CI database is ephemeral and isolated from production. No production database credential is used. The workflow still has read-only repository permissions and performs no Google operation or autonomous review action.

### Remaining limitation

This validates a real PostgreSQL instance in CI, but it does not certify an external persistent staging server. V6.34's SSH deployment remains available for that later step.
