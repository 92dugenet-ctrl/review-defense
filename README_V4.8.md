# Review Defense V4.8 — Outcome & Appeal Tracking

V4.8 adds a framework-neutral outcome tracking layer.

## Added
- Outcome records: REMOVED, REJECTED, NO_RESPONSE, APPEAL_AVAILABLE, APPEAL_REJECTED, APPEALED, CLOSED, UNKNOWN.
- Source, timestamp, actor, external reference, optional reason and notes.
- Explicit recorder permissions.
- Descriptive appeal/finality helpers; no prediction or inferred reason.
- Tenant, case and submission identity preserved.
- Outcome summary for operational analytics.
- Routes `/outcomes` and `/submissions/:id/outcomes`.

No Google action is performed. A recorded outcome is treated as an observation, not proof of Google's internal reasoning.
