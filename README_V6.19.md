# Review Defense V6.19 — Collaborative Contradiction History & Evidence Matrix

V6.19 extends V6.18 with append-only human disposition history and a read-only claim/evidence matrix.

## Implemented
- Append-only `contradiction_disposition_history` with tenant RLS.
- `GET /v1/cases/{case_id}/contradictions/{contradiction_id}/history`.
- `GET /v1/cases/{case_id}/evidence-matrix`.
- Every human disposition is retained in history; the current disposition remains separately queryable.
- Matrix links claims to the evidence referenced by contradictions and preserves evidence SHA-256/verification metadata when available.
- Matrix and history are read-only projections and always report `requires_human_review=true`.
- No disposition removes the underlying contradiction.

## Security invariants
- Tenant isolation and server-side RBAC remain enforced.
- PostgreSQL RLS protects history rows.
- Evidence integrity metadata is preserved; no evidence content is rewritten.
- No Google deletion, reporting, reply, or other external mutation is introduced.
- Existing decision/freeze/approval/submission gates remain unchanged.

## Limitation
The matrix currently links evidence through detected contradiction findings; it does not yet provide a manually authored many-to-many claim/evidence annotation layer. History is append-only but not yet a collaborative commenting/thread system.
