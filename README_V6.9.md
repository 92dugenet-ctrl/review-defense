# Review Defense V6.9 — SLA Controls & Escalation Signals

V6.9 adds explicit, auditable SLA controls while preserving human control over every operational decision.

## Implemented
- SLA pause/resume controls at case level.
- Pause requires an explicit human-provided reason.
- Paused time is excluded from the effective SLA clock.
- Queue SLA payloads now expose `PAUSED` state and escalation level.
- Escalation levels are deterministic: `NONE`, `DUE`, `CRITICAL` after material overdue time.
- `GET /v1/cases/{case_id}/sla` exposes the current SLA state.
- `POST /v1/cases/{case_id}/pause-sla` and `/resume-sla` are role-protected.
- Audit events are emitted for pause/resume.
- PostgreSQL persistence added for pause timestamp, accumulated pause seconds and reason.
- Tenant isolation is enforced through the existing organization-scoped case lookup and PostgreSQL RLS boundary.

## Security invariants
- No automatic reassignment.
- No automatic escalation action or external notification is performed; V6.9 exposes an auditable signal only.
- No automatic freeze, decision, approval or submission.
- No Google deletion, reporting or response action is introduced or automated.
- Evidence SHA-256 integrity and human verification boundaries remain unchanged.

## Limitation
SLA clocks still use deterministic elapsed time rather than business calendars/holidays. Escalation is a state signal, not an automatic notification or reassignment workflow.
