"""V4.7 Submission & Appeal Workspace.

Framework-neutral contracts for preparing, approving and tracking review reports
and appeals. No external Google action is performed here.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from typing import Literal

SubmissionKind = Literal["INITIAL_REPORT", "APPEAL"]
SubmissionStatus = Literal[
    "DRAFT", "PENDING_APPROVAL", "APPROVED", "SUBMITTED",
    "UNDER_REVIEW", "REJECTED", "APPEAL_ELIGIBLE", "APPEALED", "CLOSED",
    "INVALIDATED"
]

APPROVER_ROLES = {"OWNER", "ADMIN", "ANALYST"}

@dataclass(frozen=True)
class SubmissionRecord:
    submission_id: str
    case_id: str
    organization_id: str
    kind: SubmissionKind
    content: str
    created_at: str
    created_by: str
    status: SubmissionStatus = "DRAFT"
    content_sha256: str | None = None
    approved_at: str | None = None
    approved_by: str | None = None
    submitted_at: str | None = None
    external_reference: str | None = None
    invalidated_at: str | None = None
    invalidation_reason: str | None = None

@dataclass(frozen=True)
class SubmissionApproval:
    approval_id: str
    submission_id: str
    organization_id: str
    actor_id: str
    actor_role: str
    approved_at: str
    content_sha256: str

@dataclass(frozen=True)
class SubmissionWorkspace:
    organization_id: str
    submission: SubmissionRecord
    approvals: tuple[SubmissionApproval, ...] = ()


def content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


def create_submission(*, submission_id: str, case_id: str, organization_id: str,
                      kind: SubmissionKind, content: str, created_at: str,
                      created_by: str) -> SubmissionRecord:
    if not submission_id or not case_id or not organization_id or not created_by:
        raise ValueError("submission identity fields are required")
    if not content.strip():
        raise ValueError("submission content is required")
    if kind not in {"INITIAL_REPORT", "APPEAL"}:
        raise ValueError("unsupported submission kind")
    return SubmissionRecord(submission_id, case_id, organization_id, kind,
                            content, created_at, created_by)


def prepare_submission(submission: SubmissionRecord) -> SubmissionRecord:
    if submission.status not in {"DRAFT", "INVALIDATED"}:
        raise ValueError("submission is not editable in its current state")
    return replace(submission, status="DRAFT", content_sha256=content_hash(submission.content),
                   approved_at=None, approved_by=None, submitted_at=None,
                   external_reference=None, invalidated_at=None, invalidation_reason=None)


def request_approval(submission: SubmissionRecord) -> SubmissionRecord:
    if submission.status != "DRAFT" or not submission.content_sha256:
        raise ValueError("submission must be prepared before approval")
    if submission.kind == "APPEAL" and not submission.content.strip():
        raise ValueError("appeal content is required")
    return replace(submission, status="PENDING_APPROVAL")


def approve_submission(*, submission: SubmissionRecord, actor_id: str, actor_role: str,
                       approval_id: str, approved_at: str) -> tuple[SubmissionRecord, SubmissionApproval]:
    if actor_role not in APPROVER_ROLES:
        raise PermissionError("role cannot approve submissions")
    if submission.status != "PENDING_APPROVAL" or not submission.content_sha256:
        raise ValueError("submission is not pending approval")
    if content_hash(submission.content) != submission.content_sha256:
        raise ValueError("submission content integrity check failed")
    approved = replace(submission, status="APPROVED", approved_at=approved_at,
                       approved_by=actor_id)
    event = SubmissionApproval(approval_id, submission.submission_id,
                               submission.organization_id, actor_id, actor_role,
                               approved_at, submission.content_sha256)
    return approved, event


def invalidate_if_modified(*, submission: SubmissionRecord, modified_content: str,
                            invalidated_at: str, reason: str = "content_modified") -> SubmissionRecord:
    if not submission.content_sha256:
        return submission
    if content_hash(modified_content) == submission.content_sha256:
        return submission
    if submission.status in {"PENDING_APPROVAL", "APPROVED"}:
        return replace(submission, content=modified_content, status="INVALIDATED",
                       invalidated_at=invalidated_at, invalidation_reason=reason,
                       approved_at=None, approved_by=None)
    return replace(submission, content=modified_content)


def mark_submitted(*, submission: SubmissionRecord, submitted_at: str,
                   external_reference: str) -> SubmissionRecord:
    """Record an externally performed submission; does not perform it."""
    if submission.status != "APPROVED":
        raise ValueError("only approved submissions can be marked submitted")
    if not external_reference.strip():
        raise ValueError("external reference is required")
    if content_hash(submission.content) != submission.content_sha256:
        raise ValueError("submission content integrity check failed")
    return replace(submission, status="SUBMITTED", submitted_at=submitted_at,
                   external_reference=external_reference)


def update_status(*, submission: SubmissionRecord, status: SubmissionStatus) -> SubmissionRecord:
    allowed = {"SUBMITTED", "UNDER_REVIEW", "REJECTED", "APPEAL_ELIGIBLE", "APPEALED", "CLOSED"}
    if status not in allowed:
        raise ValueError("status can only be advanced through outcome tracking")
    if status == "SUBMITTED" and submission.status != "APPROVED":
        raise ValueError("submission must be approved before submission tracking")
    if status != "SUBMITTED" and submission.status not in {"SUBMITTED", "UNDER_REVIEW", "APPEAL_ELIGIBLE", "APPEALED"}:
        raise ValueError("invalid outcome transition")
    return replace(submission, status=status)


def can_edit_submission(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST"}


def can_approve_submission(role: str) -> bool:
    return role in APPROVER_ROLES


def can_record_external_submission(role: str) -> bool:
    return role in APPROVER_ROLES
