"""Cases workspace assembly seam.

Builds the existing read-only workspace representation without owning HTTP,
authorization, persistence, or state transitions.
"""
from __future__ import annotations

from typing import Any

from ..reviews.review_workspace import extract_claims, classify_policy_signals
from ..api.operations_ui import (
    ReviewSummary, ClaimView, PolicySignalView, EvidenceView, TimelineEvent,
    Contradiction, CaseWorkspace, missing_evidence_tasks,
)


class CaseWorkspaceService:
    @staticmethod
    def build(case: Any, review: Any, evidence_rows: list[dict[str, Any]],
              audit_rows: list[dict[str, Any]], stored_contradictions: list[dict[str, Any]]):
        claims = extract_claims(review)
        signals = classify_policy_signals(claims)
        evidence = tuple(
            EvidenceView(
                e["evidence_id"], e["filename"], e.get("content_type") or "UNKNOWN",
                e["sha256"], "VERIFIED" if e.get("verified") else "UNVERIFIED",
            )
            for e in evidence_rows
        )
        claim_views = tuple(ClaimView(c.claim_id, c.text, c.claim_type, "UNVERIFIED") for c in claims)
        policy_views = tuple(PolicySignalView(s.code, s.status, s.justification) for s in signals)
        timeline = tuple(
            TimelineEvent(a["event_id"], a["at"], a["action"], a.get("actor_id") or "system", "AUDIT")
            for a in audit_rows
        )
        required = {}
        for signal in signals:
            for claim_id in signal.claim_ids:
                required.setdefault(claim_id, []).extend(signal.evidence_required)
        base_workspace = CaseWorkspace(
            case.case_id, case.organization_id, case.status,
            "HIGH" if signals else "NORMAL",
            ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
            claim_views, policy_views, evidence, timeline, (), 0.0,
        )
        tasks = missing_evidence_tasks(base_workspace, required)
        coverage = 1.0 if not tasks else max(
            0.0,
            len({t.evidence_requirement for t in tasks if t.status != "OPEN"})
            / max(1, len({r for rs in required.values() for r in rs})),
        )
        contradiction_views = tuple(
            Contradiction(
                c["contradiction_id"], c["description"], c["claim_id"],
                tuple(c["evidence_ids"]), bool(c.get("requires_human_review", True)),
            )
            for c in stored_contradictions
        )
        workspace = CaseWorkspace(
            case.case_id, case.organization_id, case.status,
            "HIGH" if signals or contradiction_views else "NORMAL",
            ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
            claim_views, policy_views, evidence, timeline, contradiction_views, coverage,
        )
        return workspace, tasks
