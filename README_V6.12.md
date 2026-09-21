# Review Defense V6.12 — Controlled Notification Delivery

V6.12 completes the V6.11 outbox boundary with explicit, human-triggered delivery adapters for `IN_APP`, `EMAIL`, and `WEBHOOK` notifications.

## Implemented
- `POST /v1/notifications/{id}/deliver` performs one explicit delivery attempt.
- Only `OWNER`/`ADMIN` may trigger delivery.
- Email uses server-side SMTP configuration supplied to the API; credentials are never accepted from request bodies.
- HTTPS webhooks use SSRF protections: no credentials in URL, no localhost/private/link-local/reserved/multicast/metadata targets.
- Delivery attempts, failures and successful delivery are persisted/audited.
- Failed delivery remains `PENDING` so an operator can retry or cancel it.
- Successful delivery becomes `SENT`.
- `IN_APP` delivery remains local and performs no network I/O.
- PostgreSQL stores attempt count, last attempt and last error.

## Security invariants
- Tenant isolation and PostgreSQL RLS are unchanged.
- Google review deletion/reporting/reply APIs are not called.
- Existing human approval gates for Google actions are unchanged.
- Evidence SHA-256 integrity and decision/freeze/approval/submission controls are unchanged.
- No automatic notification worker or background sender is introduced; delivery requires an explicit authenticated operator action.

## Limitation
SMTP and webhook delivery are real adapters, but this release intentionally does not add a background scheduler/worker. Delivery is an explicit operator action so outbound side effects remain observable and controllable.
