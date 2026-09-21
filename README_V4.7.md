# Review Defense V4.7 — Submission & Appeal Workspace

V4.7 adds framework-neutral submission and appeal preparation contracts.

## Guarantees
- Initial reports and appeals are distinct submission kinds.
- Content is hashed before approval.
- Only OWNER/ADMIN/ANALYST can approve.
- Content modification invalidates pending/approved submissions.
- External submission is **recorded only** through `mark_submitted`; this module never calls Google or another external service.
- Outcome tracking is separate from external action.
- Organization identity is preserved on all records/events.
- No removal probability is calculated.

## Workflow

`DRAFT → PENDING_APPROVAL → APPROVED → SUBMITTED → UNDER_REVIEW → REJECTED / APPEAL_ELIGIBLE / CLOSED`

Appeals use a separate `SubmissionRecord(kind="APPEAL")`.

This remains a framework-neutral reference/application layer, not a deployed browser UI.
