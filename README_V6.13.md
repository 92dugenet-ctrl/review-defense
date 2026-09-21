# Review Defense V6.13 — Bounded Notification Delivery Worker

V6.13 adds an invocation-driven, tenant-scoped delivery worker on top of V6.12.
It provides bounded retries, exponential backoff, dead-letter state and idempotent
single-run processing without starting a scheduler or background thread itself.

## Implemented
- `src/notification_worker.py` provides `NotificationWorker.run_once()`.
- `POST /v1/notifications/worker/run` lets an authenticated `OWNER`/`ADMIN` run a bounded batch for their tenant.
- Default batch size is 25; maximum is 100.
- Retry backoff is bounded: 60s, 300s, 1500s, then capped at 3600s.
- Successful delivery becomes `SENT`.
- Failed delivery remains `PENDING` until the retry budget is exhausted.
- Exhausted notifications receive `dead_lettered_at` and stop retrying automatically.
- Future retry timestamps are respected; the worker skips notifications that are not due.
- Tenant filtering is mandatory in the worker API and implementation.
- Every retry, dead-letter and worker run is auditable.
- PostgreSQL migration `013_v613_notification_worker.sql` adds worker state and an index.
- The existing V6.12 delivery adapters are reused; no new Google integration exists.

## Security invariants
- Tenant isolation and PostgreSQL RLS remain unchanged.
- Only `OWNER`/`ADMIN` can invoke the worker endpoint.
- The worker never starts a scheduler or thread by itself.
- Outbound delivery still uses the V6.12 SSRF-safe webhook and server-side SMTP controls.
- Google review deletion/reporting/reply APIs are not called.
- Existing human approval gates for Google actions are unchanged.
- Evidence SHA-256 integrity and decision/freeze/approval/submission controls are unchanged.

## Limitation
V6.13 provides a production-ready worker primitive and an explicit authenticated run endpoint,
but it does not install a perpetual scheduler. An external scheduler may invoke the endpoint or
worker according to an organization's operational policy. This keeps autonomous outbound side effects
explicitly controlled.
