# Review Defense V6.8 — SLA & Analyst Workload

V6.8 adds a deterministic SLA layer to the V6.7 analyst queue without introducing automated case assignment or external Google actions.

## Implemented
- `src/review_sla.py` defines auditable SLA windows by queue priority: CRITICAL 4h, HIGH 12h, NORMAL 24h, LOW 72h.
- Queue items expose `due_at`, `status`, remaining hours and SLA window.
- `GET /v1/review-queue/workload` returns tenant-scoped workload buckets for assigned analysts and unassigned work.
- Workload includes case count, aggregate priority score, critical/high counts and SLA overdue/due-soon counts.
- Existing manual claim/unclaim controls remain authoritative; V6.8 does not auto-assign cases.
- PostgreSQL migration `008_v68_sla_workload.sql` adds a supporting index while SLA due times remain derived, preventing stale duplicated state.

## Security invariants
- Tenant isolation and server-side RBAC remain enforced.
- No automatic freeze, decision, approval or submission is introduced.
- No Google deletion, reporting or response action is introduced or automated.
- Evidence SHA-256 integrity and audit events are unchanged.

## Limitation
SLA clocks use case `created_at` and deterministic priority. There is no business-calendar/holiday engine, pause state, escalation notification service, or automatic reassignment yet.
