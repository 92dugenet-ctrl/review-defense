# Review Defense V6.18 — Human Contradiction Disposition

V6.18 adds an explicit, auditable analyst disposition layer for structured contradiction findings.

## Implemented
- `src/contradiction_disposition.py` validates four human dispositions:
  - `CONFIRMED_CONTRADICTION`
  - `EXPLAINED`
  - `FALSE_POSITIVE`
  - `NEEDS_MORE_EVIDENCE`
- Every disposition requires a rationale and is tenant-scoped.
- `GET /v1/cases/{case_id}/contradictions` now exposes the current disposition when present.
- `POST /v1/cases/{case_id}/contradictions/{contradiction_id}/disposition` records a human disposition.
- Only OWNER/ADMIN/ANALYST may disposition findings.
- PostgreSQL persistence and RLS via `016_v618_contradiction_dispositions.sql`.
- Audit event `CONTRADICTION_DISPOSITIONED` records the transition.
- Dispositions never erase the underlying contradiction finding and never auto-approve, freeze, submit, delete, report, or reply to Google.

## Security invariants
- Tenant isolation remains mandatory in memory and PostgreSQL/RLS.
- RBAC remains server-side.
- A disposition is evidence of a human review action, not an automated resolution.
- The API continues to report `requires_human_review=true` for contradiction data.
- Google review deletion/reporting/reply APIs are not called.
- Existing human approval gates and evidence SHA-256 integrity are unchanged.

## Limitation
V6.18 records a single current disposition per contradiction. It does not yet provide a full collaborative history/version browser or claim-by-claim evidence matrix. Those can be layered on without changing the human-gated external-action boundary.
