# Review Defense V6.6 — Evidence Fact Extraction & Review Queue

V6.6 adds a deterministic, conservative evidence-extraction layer on top of V6.5.

## Implemented
- `src/evidence_extraction.py` extracts bounded fact suggestions from explicitly readable UTF-8 text evidence (`text/plain`, `text/csv`, `application/json`).
- Supported fact classes mirror the contradiction engine: amounts, durations and dates.
- Suggestions have stable IDs, source line locations and confidence scores.
- Suggestions are **never verified automatically** and cannot directly create decisions, freezes, approvals or submissions.
- `POST /v1/cases/:id/extract-facts` performs tenant-scoped extraction for case evidence and records an audit event.
- Evidence SHA-256 is checked before extraction; integrity failures stop processing.
- Case Workspace exposes unverified fact suggestions for analyst review.
- PostgreSQL migration `006_v66_fact_suggestions.sql` persists suggestions with RLS.
- PostgreSQL repository supports durable suggestion storage.
- Unsupported binary/PDF/image evidence is deliberately not interpreted by this deterministic extractor.
- Existing human approval, tenant isolation, RBAC, auditability, evidence integrity and Google-action prohibitions remain intact.

## Security invariants
- Extraction is read-only with respect to evidence objects.
- No suggestion is promoted to a verified evidence fact without the existing explicit human verification flow.
- No Google deletion, reporting or review-response action is introduced or automated.
- Contradictions remain human-gated.

## Validation
- Full regression suite: **189 passed**.
- Python compilation of `src/` and `tests/`: passed.

## Limitation
The extractor is intentionally conservative and text-only. It does not OCR images, parse arbitrary PDFs, or infer facts from unstructured binary content. Those capabilities can be added later behind an explicit extraction/verification boundary.
