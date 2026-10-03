"""Application seam for the read-only Cases evidence matrix."""
from __future__ import annotations

from typing import Any

from .case_review_matrix import build_evidence_matrix
from .review_workspace import extract_claims


class CaseEvidenceMatrixService:
    def __init__(self, *, store: Any):
        self.store = store

    def build(self, *, organization_id: str, case: Any) -> list[dict[str, Any]]:
        review = self.store.reviews.get((organization_id, case.review_id))
        if review is None:
            raise KeyError("review not found")
        claims = extract_claims(review)
        evidence = [
            row for (org, _), row in self.store.evidence.items()
            if org == organization_id and row.get("case_id") == case.case_id
        ]
        contradictions = self.store.contradictions.get((organization_id, case.case_id), [])
        return build_evidence_matrix(
            claims=claims,
            evidence=evidence,
            contradictions=contradictions,
            dispositions=self.store.contradiction_dispositions,
        )
