# Review Defense V6.15 — Notification Observability

V6.15 adds read-only, tenant-scoped operational observability for the notification outbox and V6.13 delivery worker.

## Implemented
- `src/notification_observability.py` derives notification status/channel/level counts, delivery attempts, success/failure/retry events, dead letters, policy blocks, queue events and worker runs.
- `GET /v1/notifications/metrics` exposes these metrics to authenticated tenant users (`OWNER`, `ADMIN`, `ANALYST`).
- PostgreSQL-backed notifications are loaded through the existing tenant-scoped repository before metrics are calculated.
- Metrics are derived from existing notification state and audit events; no new mutable telemetry store is introduced.
- Added four V6.15 regression tests.

## Security invariants
- Metrics are strictly filtered by the authenticated organization ID.
- The endpoint is read-only and performs no external I/O.
- No notification state is changed while calculating metrics.
- Google review deletion/reporting/reply APIs are not called.
- Existing human approval gates, evidence SHA-256 integrity, RBAC and tenant isolation remain unchanged.

## Limitation
V6.15 provides in-process operational metrics only. It does not add an external metrics backend, dashboard, alerting service, or autonomous scheduler.
