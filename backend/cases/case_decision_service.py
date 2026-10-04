"""Cases decision/freeze/approval application seam.

Owns decision lifecycle orchestration and persistence side effects while keeping
HTTP parsing, authorization and response serialization in the API layer.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable
from uuid import uuid4

from .decision_workspace import (
    ApprovalEvent,
    DecisionRecord,
    DossierSnapshot,
    approve_decision,
    attach_snapshot,
    create_decision,
    freeze_dossier,
    request_approval,
)
from ..reviews.review_workspace import classify_policy_signals, extract_claims
from ..authentication.security_hardening import utc_now


class CaseDecisionService:
    """Application seam for case decision, dossier freeze and approval state."""

    def __init__(self, *, store: Any, repository: Any = None,
                 audit_event: Callable[..., Any] | None = None):
        self.store = store
        self.repository = repository
        self.audit_event = audit_event

    def create(self, *, case: Any, user_id: str, kind: str, rationale: str) -> DecisionRecord:
        decision = create_decision(
            decision_id=str(uuid4()),
            case_id=case.case_id,
            organization_id=case.organization_id,
            kind=kind,
            rationale=rationale,
            created_at=utc_now().isoformat(),
            created_by=user_id,
        )
        self.store.decisions[(case.organization_id, decision.decision_id)] = decision
        if self.repository is not None:
            self.repository.put_decision(case.organization_id, asdict(decision))
        case.decision_id = decision.decision_id
        case.status = "ANALYZED"
        if self.repository is not None:
            self.repository.update_case(
                case.organization_id,
                case.case_id,
                status=case.status,
                decision_id=case.decision_id,
            )
        if self.audit_event is not None:
            self.audit_event(
                case.organization_id,
                user_id,
                "DECISION_CREATED",
                f"case:{case.case_id}",
            )
        return decision

    def freeze(self, *, case: Any, user_id: str) -> tuple[DecisionRecord, DossierSnapshot]:
        decision = self.store.decisions[(case.organization_id, case.decision_id)]
        review = self.store.reviews[(case.organization_id, case.review_id)]
        claims = [asdict(item) for item in extract_claims(review)]
        signals = [asdict(item) for item in classify_policy_signals(extract_claims(review))]
        payload = {
            "case": asdict(case),
            "review": asdict(review),
            "claims": claims,
            "policy_signals": signals,
            "decision": asdict(decision),
        }
        snapshot = freeze_dossier(
            case_id=case.case_id,
            organization_id=case.organization_id,
            payload=payload,
            frozen_at=utc_now().isoformat(),
            frozen_by=user_id,
        )
        decision = request_approval(attach_snapshot(decision, snapshot))
        self.store.snapshots[(case.organization_id, case.case_id)] = snapshot
        self.store.decisions[(case.organization_id, case.decision_id)] = decision
        case.snapshot_sha256 = snapshot.sha256
        case.status = "HUMAN_REVIEW"
        if self.repository is not None:
            self.repository.put_snapshot(
                case.organization_id,
                case.case_id,
                snapshot.sha256,
                payload,
                user_id,
                snapshot.frozen_at,
            )
            self.repository.put_decision(case.organization_id, asdict(decision))
            self.repository.update_case(
                case.organization_id,
                case.case_id,
                status=case.status,
                snapshot_sha256=case.snapshot_sha256,
            )
        if self.audit_event is not None:
            self.audit_event(
                case.organization_id,
                user_id,
                "DOSSIER_FROZEN",
                f"case:{case.case_id}",
                sha256=snapshot.sha256,
            )
        return decision, snapshot

    def approve(self, *, case: Any, user_id: str, user_role: str) -> tuple[DecisionRecord, ApprovalEvent]:
        decision = self.store.decisions[(case.organization_id, case.decision_id)]
        snapshot = self.store.snapshots[(case.organization_id, case.case_id)]
        approved, event = approve_decision(
            decision=decision,
            snapshot=snapshot,
            actor_id=user_id,
            actor_role=user_role,
            approval_id=str(uuid4()),
            approved_at=utc_now().isoformat(),
        )
        self.store.decisions[(case.organization_id, case.decision_id)] = approved
        case.status = "READY_TO_SUBMIT"
        self.store.approvals.append(event)
        if self.repository is not None:
            self.repository.put_decision(case.organization_id, asdict(approved))
            self.repository.put_approval(case.organization_id, asdict(event))
            self.repository.update_case(
                case.organization_id,
                case.case_id,
                status=case.status,
            )
        if self.audit_event is not None:
            self.audit_event(
                case.organization_id,
                user_id,
                "DECISION_APPROVED",
                f"case:{case.case_id}",
            )
        return approved, event
