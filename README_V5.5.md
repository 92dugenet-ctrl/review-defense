# Review Defense V5.5 — Performance, Concurrency & Resilience

V5.5 adds framework-neutral controls for protecting the application from
transient provider/database failures, duplicate requests, overload and
cascading failures.

## Added

- bounded exponential retry with an explicit retryable-exception allowlist;
- retry exhaustion that preserves the last exception;
- operation deadlines with monotonic-clock semantics;
- atomic in-memory idempotency barrier for concurrent duplicate requests;
- idempotency conflict detection when a key is reused for different payloads;
- circuit breaker with CLOSED / OPEN / HALF_OPEN states and a single recovery probe;
- bounded concurrency gate (bulkhead) with active/peak tracking;
- rolling-window throughput limiter;
- concurrency and failure-path tests.

## Safety boundaries

- No retry of validation or permission errors by default.
- No automatic Google action is introduced.
- Idempotency is a protection against duplicate execution, not a substitute for
  a durable database uniqueness constraint in production.
- In-memory controls are reference implementations; production deployment
  should use shared/durable coordination where multiple application instances
  must enforce the same limit or idempotency key.
- Circuit breaking and retries must be configured per dependency and bounded by
  an overall request deadline.

## Production adapter guidance

Use these primitives around PostgreSQL transactions, private object storage,
Google adapters or background jobs. For horizontally scaled workers, move
idempotency state, rate/concurrency coordination and circuit state to an
appropriate shared system when cross-instance guarantees are required.
