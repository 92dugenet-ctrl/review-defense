# Review Defense V5.6 — Background Jobs & Asynchronous Processing

V5.6 adds a durable, framework-neutral background-job layer for analyses,
evidence processing and other asynchronous work.

## Implemented

- SQLite-backed persistent job queue reference adapter;
- priority-aware scheduling;
- explicit job states: QUEUED, RUNNING, SUCCEEDED, RETRY_SCHEDULED,
  DEAD_LETTER, CANCELLED;
- tenant-scoped idempotency keys and payload fingerprint conflict detection;
- worker leases with recovery of expired RUNNING jobs;
- bounded retry attempts and persistent last-error information;
- dead-letter queue inspection;
- synchronous worker harness with handler dispatch;
- concurrent claim protection;
- tenant isolation for job retrieval/cancellation;
- persistence across process/object re-instantiation.

## Safety boundaries

- Jobs never call Google or any external service by themselves.
- External submissions remain explicit application actions requiring the existing
  approval workflow.
- Retries are bounded; production handlers should classify transient versus
  permanent errors and apply the V5.5 resilience primitives where appropriate.
- SQLite is a reference adapter. A horizontally scaled production deployment
  should use PostgreSQL (or another durable queue) with transactional claiming,
  row locking, worker heartbeats and operational monitoring.
- Lease recovery can cause at-least-once execution; handlers must therefore be
  idempotent and use durable idempotency keys where side effects exist.

## Production adapter guidance

Use the same job contract for review ingestion, claim analysis, evidence hashing,
policy analysis and report preparation. Keep the Google adapter outside the
worker core and preserve human approval before any external submission.
