# Review Defense V6.11 — Escalation Notification Outbox & Delivery Controls

V6.11 adds an auditable, tenant-scoped notification outbox for human-controlled escalation communications. The API queues notifications but performs **no network I/O** and cannot mutate Google resources.

## Implemented
- `src/notification_outbox.py` defines validated notification records and stable tenant-scoped dedupe keys.
- `GET /v1/notifications` lists tenant-scoped notifications, with optional `status` filtering.
- `POST /v1/escalations/{case_id}/notify` queues an escalation notification for an existing open/acknowledged escalation.
- Supported channels: `IN_APP`, `EMAIL`, `WEBHOOK`.
- Only `OWNER`/`ADMIN` can queue, cancel or mark a notification sent; `ANALYST` can view the queue but cannot create an external notification.
- Duplicate pending notifications are safely deduplicated by tenant/case/escalation/channel/target.
- `POST /v1/notifications/{id}/cancel` provides explicit human cancellation.
- `POST /v1/notifications/{id}/mark-sent` records a human-confirmed delivery state; it does not send anything.
- PostgreSQL persistence via `notification_outbox` and RLS tenant isolation.
- Audit events are written for queue, cancellation and sent-state transitions.

## Security invariants
- Tenant isolation remains enforced in memory and PostgreSQL/RLS.
- No notification endpoint executes network I/O.
- No Google deletion, reporting, reply, or other external Google mutation is introduced.
- Google actions remain behind the existing human approval gates.
- Evidence SHA-256 integrity and all existing decision/freeze/approval/submission controls are unchanged.

## Limitation
V6.11 stops at a durable, auditable outbox. A future delivery adapter may consume the outbox, but actual email/webhook delivery is intentionally not implemented here. `mark-sent` is an explicit human record of delivery and must not be interpreted as an automatic send.
