# Review Defense V6.14 — Notification Policies

V6.14 adds tenant-scoped notification policy controls on top of the V6.13 bounded delivery worker.
Policies constrain escalation notification creation and delivery without performing network I/O themselves.

## Implemented
- `src/notification_policy.py` validates tenant notification policies.
- Policies control enabled escalation levels (`DUE`, `CRITICAL`).
- Policies control allowed channels (`IN_APP`, `EMAIL`, `WEBHOOK`).
- External channels can be disabled with `allow_external=false`.
- Optional quiet window blocks notification delivery during the configured time interval.
- `GET /v1/organization/notification-policy` reads the tenant policy.
- `POST /v1/organization/notification-policy` updates the tenant policy; OWNER/ADMIN only.
- Notification queueing enforces the policy.
- Manual delivery enforces the policy.
- V6.13 worker delivery enforces the policy.
- Policy blocks are auditable.
- PostgreSQL persistence and RLS via `014_v614_notification_policies.sql`.
- Existing behavior is preserved by the default policy: all existing levels/channels remain enabled and external delivery remains allowed until an organization explicitly configures a restriction.

## Security invariants
- Tenant isolation remains mandatory in memory and PostgreSQL/RLS.
- RBAC remains server-side.
- Policy configuration cannot mutate Google resources.
- Google review deletion/reporting/reply APIs are not called.
- Existing human approval gates for Google actions are unchanged.
- Evidence SHA-256 integrity and decision/freeze/approval/submission controls are unchanged.

## Limitation
Quiet hours currently use UTC for evaluation rather than the tenant's business-calendar timezone. The policy engine is intentionally configuration-only: it does not add an autonomous scheduler. V6.13's explicit worker invocation remains the mechanism that causes delivery attempts.
