# Review Defense V6.10 — Business Calendar & SLA Escalation Workflow

V6.10 adds tenant-configurable business-hour SLA arithmetic and an explicit, human-operated escalation workflow. It preserves V6.4 Case Workspace, V6.5 contradictions, V6.6 extraction, V6.7 queue, V6.8 workload and V6.9 pause/resume controls.

## Implemented
- `src/business_calendar.py` supports tenant timezone, workdays, office hours and holiday dates.
- `src/review_sla.py` calculates SLA against business hours while preserving a 24/7 default for backward compatibility.
- Paused SLA time is excluded using the configured business calendar.
- `GET/POST /v1/organization/sla-calendar` exposes explicit calendar configuration.
- Queue and case SLA payloads include calendar metadata.
- `src/escalation_workflow.py` creates deterministic `DUE`/`CRITICAL` signals only when an SLA is breached.
- `GET /v1/escalations` exposes tenant-scoped signals.
- `POST /v1/escalations/{case_id}/acknowledge` and `/resolve` provide human-controlled workflow transitions.
- All escalation transitions are audited and persisted by the PostgreSQL adapter when available.
- Migration `010_v610_business_calendar.sql` adds calendar and escalation persistence.

## Security invariants
- Tenant isolation and server-side RBAC remain enforced.
- Evidence SHA-256 integrity is unchanged.
- Escalations never auto-assign, auto-freeze, auto-approve, auto-submit or call Google.
- No Google deletion, reporting or response action is introduced or automated.

## Limitation
The default calendar remains 24/7 to preserve V6.9 behavior until a tenant explicitly configures office hours. Escalation delivery is intentionally an in-app audited workflow; email/Slack/SMS notification is not automated in V6.10.
