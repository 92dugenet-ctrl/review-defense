# Review Defense V6.7 — Analyst Review Queue & Assignment

V6.7 adds a deterministic analyst review queue on top of the V6.4 workspace, V6.5 contradiction engine and V6.6 evidence fact suggestions.

## Implemented
- `src/review_queue.py` provides bounded, deterministic priority scoring.
- Queue priority considers strong/relevant policy signals, contradictions, missing evidence tasks, unverified fact suggestions and case age.
- Queue priorities are `LOW`, `NORMAL`, `HIGH`, `CRITICAL` and scores are capped at 100.
- `GET /v1/review-queue` returns tenant-scoped queue items with explicit priority reasons.
- `POST /v1/review-queue/:case_id/claim` assigns a case to the authenticated analyst/manager.
- `POST /v1/review-queue/:case_id/unclaim` releases an assignment, with manager override.
- Assign/unassign actions are audit logged.
- PostgreSQL migration `007_v67_review_queue.sql` persists `api_cases.assigned_to` and adds a tenant-scoped assignment index.
- PostgreSQL repository exposes `assign_case`.
- Existing case workspace, contradiction findings and fact suggestions remain unchanged and are used as queue inputs.

## Security invariants
- Queue and assignment operations are tenant-scoped.
- Only `OWNER`, `ADMIN` and `ANALYST` can claim/unclaim cases.
- A case assigned to another analyst cannot be claimed by a peer.
- Managers can unclaim a case when operationally necessary.
- Queue scoring never creates or approves decisions.
- Human approval remains mandatory before any external Google action.
- No Google deletion, reporting or review-response action is introduced or automated.
- Evidence SHA-256 integrity, RLS and existing RBAC boundaries remain intact.

## Validation
- Full regression suite: **194 passed**.
- Python compilation of `src/` and `tests/`: passed.

## Limitation
The queue is deterministic and explainable rather than ML-ranked. SLA age is calculated from the case creation timestamp, and missing-evidence weighting uses the requirements already exposed by the current workspace. Future versions can add durable SLA policies, team capacity balancing and richer assignment rules without changing the security boundary.
