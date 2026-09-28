"""V5.3 end-to-end reference pipeline.

Composes the existing Review Defense application-layer contracts into a single
framework-neutral flow suitable for integration tests and later API adapters.
It intentionally never calls Google or any external provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .decision_workspace import (
    approve_decision, attach_snapshot, create_decision, freeze_dossier,
    invalidate_if_modified, request_approval, snapshot_matches,
)
from .evidence_vault import InMemoryObjectStore, verify_integrity
from .operations_ui import (
    CaseWorkspace, ClaimView, EvidenceView, PolicySignalView, ReviewSummary,
    case_requires_human_review, create_evidence_document, missing_evidence_tasks,
    role_can_verify_evidence,
)
from .outcome_workspace import record_outcome
from .review_workspace import ReviewContext, build_review_workspace
from .security_hardening import (
    Session, generate_session_token, require_tenant, utc_now as security_now,
)
from .submission_workspace import (
    approve_submission, create_submission, mark_submitted, prepare_submission,
    request_approval as request_submission_approval,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ExternalSubmissionGateway:
    """Explicit boundary: tests can record an external ref but cannot perform it."""
    submit: Callable[[str], str] | None = None

    def is_configured(self) -> bool:
        return self.submit is not None

    def submit_approved(self, content: str) -> str:
        if self.submit is None:
            raise RuntimeError("external submission gateway is not configured")
        return self.submit(content)


class ReviewDefenseE2E:
    """Small in-memory application harness spanning V4.4 through V5.2."""
    def __init__(self, *, organization_id: str = "org-a") -> None:
        self.organization_id = organization_id
        self.reviews: dict[str, ReviewContext] = {}
        self.workspaces = {}
        self.evidence_store = InMemoryObjectStore()
        self.evidence_documents = {}
        self.decisions = {}
        self.snapshots = {}
        self.submissions = {}
        self.outcomes = {}
        self.gateway = ExternalSubmissionGateway()
        self.external_calls = 0

    def ingest(self, review: ReviewContext):
        if review.organization_id != self.organization_id:
            raise PermissionError("organization boundary violation")
        if review.review_id in self.reviews:
            raise ValueError("duplicate review")
        if not 1 <= review.rating <= 5:
            raise ValueError("rating must be between 1 and 5")
        if not review.text.strip():
            raise ValueError("review text is required")
        self.reviews[review.review_id] = review
        workspace = build_review_workspace(review)
        self.workspaces[review.review_id] = workspace
        return workspace

    def add_evidence(self, *, evidence_id: str, review_id: str, content: bytes,
                     filename: str, content_type: str = "application/pdf"):
        review = self.reviews[review_id]
        document = create_evidence_document(
            evidence_id=evidence_id, organization_id=review.organization_id,
            filename=filename, mime_type=content_type, content=content,
            captured_at=now_iso(),
        )
        stored = self.evidence_store.put(
            organization_id=review.organization_id, evidence_id=evidence_id,
            content=content, content_type=content_type, filename=filename,
        )
        if not verify_integrity(content, stored.sha256):
            raise ValueError("stored evidence integrity check failed")
        self.evidence_documents[evidence_id] = document
        return stored

    def build_case(self, *, case_id: str, review_id: str, priority: str = "HIGH") -> CaseWorkspace:
        ws = self.workspaces[review_id]
        evidence = tuple(
            EvidenceView(evidence_id=eid, filename="evidence", evidence_type="OTHER",
                         sha256=doc.content_sha256, status="VERIFIED")
            for eid, doc in self.evidence_documents.items()
            if doc.organization_id == self.organization_id
        )
        review_summary = ReviewSummary(review_id, ws.review.rating, ws.review.text, ws.review.published_at)
        claims = tuple(ClaimView(c.claim_id, c.text, c.claim_type, c.status) for c in ws.claims)
        policies = tuple(PolicySignalView(p.code, p.status, p.justification) for p in ws.policy_signals)
        provisional = CaseWorkspace(
            case_id=case_id, organization_id=self.organization_id, state="ANALYZED",
            priority=priority, review=review_summary, claims=claims,
            policies=policies, evidence=evidence,
        )
        state = "HUMAN_REVIEW" if case_requires_human_review(provisional) else "ANALYZED"
        case = CaseWorkspace(
            case_id=case_id, organization_id=self.organization_id, state=state,
            priority=priority, review=review_summary, claims=claims,
            policies=policies, evidence=evidence,
        )
        return case

    def freeze_and_approve_decision(self, *, decision_id: str, case_id: str,
                                    payload: dict, actor_id: str = "analyst-1",
                                    actor_role: str = "ANALYST"):
        decision = create_decision(
            decision_id=decision_id, case_id=case_id,
            organization_id=self.organization_id, kind="PREPARE_REPORT",
            rationale="Policy signal requires a documented report after human review.",
            created_at=now_iso(), created_by=actor_id,
        )
        snapshot = freeze_dossier(case_id=case_id, organization_id=self.organization_id,
                                  payload=payload, frozen_at=now_iso(), frozen_by=actor_id)
        decision = attach_snapshot(decision, snapshot)
        decision = request_approval(decision)
        decision, approval = approve_decision(
            decision=decision, snapshot=snapshot, actor_id=actor_id,
            actor_role=actor_role, approval_id=f"approval-{decision_id}", approved_at=now_iso(),
        )
        self.decisions[decision_id] = decision
        self.snapshots[decision_id] = snapshot
        return decision, approval

    def invalidate_modified_dossier(self, *, decision_id: str, payload: dict):
        decision = self.decisions[decision_id]
        snapshot = self.snapshots[decision_id]
        updated = invalidate_if_modified(
            decision=decision, snapshot=snapshot, current_payload=payload,
            invalidated_at=now_iso(),
        )
        self.decisions[decision_id] = updated
        return updated

    def prepare_and_approve_submission(self, *, submission_id: str, case_id: str,
                                       content: str, actor_id: str = "analyst-1",
                                       actor_role: str = "ANALYST"):
        submission = create_submission(
            submission_id=submission_id, case_id=case_id,
            organization_id=self.organization_id, kind="INITIAL_REPORT",
            content=content, created_at=now_iso(), created_by=actor_id,
        )
        submission = prepare_submission(submission)
        submission = request_submission_approval(submission)
        submission, approval = approve_submission(
            submission=submission, actor_id=actor_id, actor_role=actor_role,
            approval_id=f"approval-{submission_id}", approved_at=now_iso(),
        )
        self.submissions[submission_id] = submission
        return submission, approval

    def record_external_submission(self, *, submission_id: str, external_reference: str,
                                   actor_role: str = "ANALYST"):
        if actor_role not in {"OWNER", "ADMIN", "ANALYST"}:
            raise PermissionError("role cannot record external submission")
        submission = self.submissions[submission_id]
        # Recording is deliberately distinct from performing an external action.
        submission = mark_submitted(
            submission=submission, submitted_at=now_iso(),
            external_reference=external_reference,
        )
        self.submissions[submission_id] = submission
        return submission

    def record_outcome(self, *, outcome_id: str, submission_id: str,
                       case_id: str, kind: str, source: str = "MANUAL"):
        outcome = record_outcome(
            outcome_id=outcome_id, organization_id=self.organization_id,
            submission_id=submission_id, case_id=case_id, kind=kind,
            recorded_at=now_iso(), recorded_by="analyst-1", source=source,
        )
        self.outcomes[outcome_id] = outcome
        return outcome

    def new_session(self, *, user_id: str = "analyst-1", role: str = "ANALYST") -> tuple[str, Session]:
        raw, token_hash = generate_session_token()
        session = Session(user_id, self.organization_id, role, token_hash,
                          security_now().replace(microsecond=0).replace(year=2099))
        return raw, session

    def authorize(self, session: Session, organization_id: str) -> None:
        require_tenant(session, organization_id)
