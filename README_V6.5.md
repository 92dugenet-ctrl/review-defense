# Review Defense V6.5 — Structured Contradiction Engine

V6.5 adds a deterministic, human-gated contradiction layer on top of the V6.4 Case Workspace.

## Implemented
- `src/contradiction_engine.py` extracts explicit claim facts for amounts, durations and dates.
- Only explicitly supplied **verified evidence facts** can produce contradiction findings.
- No binary/PDF/image content is interpreted automatically by this engine.
- Stable contradiction IDs are derived from tenant, case, claim, key and evidence IDs.
- `POST /v1/cases/:id/contradictions` runs the comparison and records an audit event.
- `GET /v1/cases/:id/contradictions` returns tenant-scoped findings.
- Case Workspace V6.4 now surfaces stored contradiction findings and keeps the human-review gate active.
- Evidence upload can carry bounded structured facts; facts are separately verified after the evidence itself is verified.
- `POST /v1/evidence/:id/facts/verify` explicitly verifies selected facts and records an audit event.
- PostgreSQL migration `005_v65_contradiction_facts.sql` adds tenant-scoped `evidence_facts` and `contradiction_findings` tables with RLS.
- PostgreSQL repository methods persist both fact and contradiction records.
- Existing SHA-256 evidence integrity, RBAC, tenant isolation, auditability and human approval workflow remain intact.
- No Google deletion, reporting or review-response action is introduced or automated.

## Validation
- Full regression suite: **185 passed**.
- Python compilation of `src/` and `tests/`: passed.

## Limitation
The contradiction engine is intentionally deterministic and conservative. It only compares explicitly structured, human-verified evidence facts against facts extracted from claim text for supported fact types. It does not claim semantic understanding of arbitrary PDFs, images or screenshots; a future evidence-extraction phase can populate structured facts for those sources.
