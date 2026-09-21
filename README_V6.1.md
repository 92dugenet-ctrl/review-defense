# Review Defense V6.1 — Production PostgreSQL API Repository

V6.1 adds the persistent application-state boundary behind the V6.0 API.

## Implemented
- PostgreSQL persistence for API sessions, reviews, cases, decisions, dossier snapshots, approvals, submissions, idempotency records and evidence metadata.
- Every repository transaction sets `SET LOCAL app.organization_id`.
- Tenant-scoped RLS policies on all new API tables.
- Atomic case creation with an audit event.
- Atomic user + membership creation.
- Persistent idempotency records scoped by organization.
- Persistent sessions with revocation and expiry fields.
- Persistent evidence metadata; object bytes remain in the V5.2 private object-store layer.
- No Google mutation is performed by this repository.

## Production requirements
Run migrations 001, 002 and 003 against PostgreSQL with TLS, backups, least-privilege credentials, connection pooling and monitoring. The test suite uses an injectable connection factory and does not require a live PostgreSQL server.
