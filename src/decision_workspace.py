"""V4.6 Decision & Approval Workspace.

Framework-neutral contracts for freezing a case dossier, recording a decision,
and obtaining explicit human approval. This module never performs an external
submission and never predicts removal outcomes.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from typing import Literal

DecisionStatus = Literal["DRAFT", "FROZEN", "PENDING_APPROVAL", "APPROVED", "INVALIDATED"]
DecisionKind = Literal["NO_ACTION", "COLLECT_EVIDENCE", "HUMAN_REVIEW", "PREPARE_REPORT", "PREPARE_APPEAL", "LEGAL_REVIEW", "URGENT_ESCALATION", "ARCHIVE"]

APPROVER_ROLES = {"OWNER", "ADMIN", "ANALYST"}

@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    case_id: str
    organization_id: str
    kind: DecisionKind
    rationale: str
    created_at: str
    created_by: str
    status: DecisionStatus = "DRAFT"
    snapshot_sha256: str | None = None
    approved_at: str | None = None
    approved_by: str | None = None
    invalidated_at: str | None = None
    invalidation_reason: str | None = None

@dataclass(frozen=True)
class DossierSnapshot:
    case_id: str
    organization_id: str
    payload: dict
    sha256: str
    frozen_at: str
    frozen_by: str

@dataclass(frozen=True)
class ApprovalEvent:
    approval_id: str
    decision_id: str
    organization_id: str
    actor_id: str
    actor_role: str
    approved_at: str
    snapshot_sha256: str

@dataclass(frozen=True)
class DecisionWorkspace:
    organization_id: str
    decision: DecisionRecord
    snapshot: DossierSnapshot | None = None
    approvals: tuple[ApprovalEvent, ...] = ()


def _canonical_payload(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def dossier_hash(payload: dict) -> str:
    return sha256(_canonical_payload(payload)).hexdigest()


def freeze_dossier(*, case_id: str, organization_id: str, payload: dict, frozen_at: str, frozen_by: str) -> DossierSnapshot:
    if not case_id or not organization_id or not frozen_by:
        raise ValueError("case_id, organization_id and frozen_by are required")
    copied = json.loads(json.dumps(payload, ensure_ascii=False))
    return DossierSnapshot(case_id, organization_id, copied, dossier_hash(copied), frozen_at, frozen_by)


def snapshot_matches(snapshot: DossierSnapshot, payload: dict) -> bool:
    return snapshot.sha256 == dossier_hash(payload)


def create_decision(*, decision_id: str, case_id: str, organization_id: str, kind: DecisionKind,
                    rationale: str, created_at: str, created_by: str) -> DecisionRecord:
    if not rationale.strip():
        raise ValueError("rationale is required")
    return DecisionRecord(decision_id, case_id, organization_id, kind, rationale,
                          created_at, created_by)


def attach_snapshot(decision: DecisionRecord, snapshot: DossierSnapshot) -> DecisionRecord:
    if decision.case_id != snapshot.case_id or decision.organization_id != snapshot.organization_id:
        raise ValueError("snapshot does not belong to decision")
    return replace(decision, status="FROZEN", snapshot_sha256=snapshot.sha256)


def request_approval(decision: DecisionRecord) -> DecisionRecord:
    if decision.status != "FROZEN" or not decision.snapshot_sha256:
        raise ValueError("decision must have a frozen dossier before approval")
    return replace(decision, status="PENDING_APPROVAL")


def approve_decision(*, decision: DecisionRecord, snapshot: DossierSnapshot, actor_id: str,
                     actor_role: str, approval_id: str, approved_at: str) -> tuple[DecisionRecord, ApprovalEvent]:
    if actor_role not in APPROVER_ROLES:
        raise PermissionError("role cannot approve decisions")
    if decision.status != "PENDING_APPROVAL":
        raise ValueError("decision is not pending approval")
    if decision.snapshot_sha256 != snapshot.sha256 or not snapshot_matches(snapshot, snapshot.payload):
        raise ValueError("frozen dossier integrity check failed")
    if decision.organization_id != snapshot.organization_id:
        raise ValueError("tenant mismatch")
    approved = replace(decision, status="APPROVED", approved_at=approved_at, approved_by=actor_id)
    event = ApprovalEvent(approval_id, decision.decision_id, decision.organization_id,
                          actor_id, actor_role, approved_at, snapshot.sha256)
    return approved, event


def invalidate_if_modified(*, decision: DecisionRecord, snapshot: DossierSnapshot, current_payload: dict,
                           invalidated_at: str, reason: str = "dossier_modified") -> DecisionRecord:
    if snapshot_matches(snapshot, current_payload):
        return decision
    if decision.status in {"APPROVED", "PENDING_APPROVAL", "FROZEN"}:
        return replace(decision, status="INVALIDATED", invalidated_at=invalidated_at,
                       invalidation_reason=reason)
    return decision


def can_create_decision(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST"}


def can_request_approval(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST"}


def can_approve_decision(role: str) -> bool:
    return role in APPROVER_ROLES


def can_submit_after_approval(role: str, decision: DecisionRecord) -> bool:
    # Submission remains outside V4.6; this helper only verifies that a caller
    # holds an approval-capable role and the decision is approved.
    return role in APPROVER_ROLES and decision.status == "APPROVED"
