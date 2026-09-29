"""V4.2/V4.3 operational UI domain contracts.

Framework-neutral reference implementation for dashboard, case workspace and
 evidence/document workspace. UI code must call application services rather
than repositories or external providers directly.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal

EvidenceStatus = Literal["UNVERIFIED", "VERIFIED", "REJECTED"]
EvidenceRelation = Literal["SUPPORTS", "CONTRADICTS", "CONTEXT"]
CaseState = Literal[
    "NEW", "ANALYZING", "ANALYZED", "EVIDENCE_NEEDED", "HUMAN_REVIEW",
    "READY_TO_SUBMIT", "SUBMITTED", "UNDER_REVIEW", "OUTCOME_RECORDED", "CLOSED"
]

@dataclass(frozen=True)
class ReviewSummary:
    review_id: str
    rating: int
    text: str
    published_at: str

@dataclass(frozen=True)
class ClaimView:
    claim_id: str
    text: str
    claim_type: str
    status: str

@dataclass(frozen=True)
class PolicySignalView:
    code: str
    status: str
    justification: str

@dataclass(frozen=True)
class EvidenceView:
    evidence_id: str
    filename: str
    evidence_type: str
    sha256: str
    status: EvidenceStatus = "UNVERIFIED"
    relations: tuple[tuple[str, EvidenceRelation], ...] = ()

@dataclass(frozen=True)
class TimelineEvent:
    event_id: str
    occurred_at: str
    kind: str
    actor: str
    source: str

@dataclass(frozen=True)
class Contradiction:
    contradiction_id: str
    description: str
    claim_id: str
    evidence_ids: tuple[str, ...]
    requires_human_review: bool = True

@dataclass(frozen=True)
class CaseWorkspace:
    case_id: str
    organization_id: str
    state: CaseState
    priority: str
    review: ReviewSummary
    claims: tuple[ClaimView, ...] = ()
    policies: tuple[PolicySignalView, ...] = ()
    evidence: tuple[EvidenceView, ...] = ()
    timeline: tuple[TimelineEvent, ...] = ()
    contradictions: tuple[Contradiction, ...] = ()
    evidence_coverage: float = 0.0

@dataclass(frozen=True)
class DashboardMetrics:
    open_cases: int
    human_review: int
    critical_alerts: int
    evidence_needed: int
    pending_approvals: int
    submissions: int
    appeals: int
    sla_at_risk: int

@dataclass(frozen=True)
class EvidenceTask:
    task_id: str
    evidence_requirement: str
    claim_id: str | None
    priority: str
    status: str = "OPEN"

@dataclass(frozen=True)
class ExtractedFact:
    value: str
    kind: str
    source_location: str
    verified: bool = False

@dataclass(frozen=True)
class EvidenceDocument:
    evidence_id: str
    organization_id: str
    filename: str
    mime_type: str
    content_sha256: str
    captured_at: str
    facts: tuple[ExtractedFact, ...] = ()


def fingerprint(content: bytes) -> str:
    return sha256(content).hexdigest()


def create_evidence_document(*, evidence_id: str, organization_id: str,
                             filename: str, mime_type: str, content: bytes,
                             captured_at: str | None = None) -> EvidenceDocument:
    ts = captured_at or datetime.now(timezone.utc).isoformat()
    return EvidenceDocument(evidence_id, organization_id, filename, mime_type,
                            fingerprint(content), ts)


def integrity_matches(document: EvidenceDocument, content: bytes) -> bool:
    return fingerprint(content) == document.content_sha256


def case_requires_human_review(case: CaseWorkspace) -> bool:
    return bool(case.contradictions) or any(p.status in {"STRONG", "RELEVANT", "POSSIBLE"} for p in case.policies)


def missing_evidence_tasks(case: CaseWorkspace, required: dict[str, list[str]]) -> list[EvidenceTask]:
    present = {e.evidence_type for e in case.evidence if e.status != "REJECTED"}
    tasks: list[EvidenceTask] = []
    for claim_id, requirements in required.items():
        for req in requirements:
            if req not in present:
                tasks.append(EvidenceTask(
                    task_id=f"REQ-{claim_id}-{req}",
                    evidence_requirement=req,
                    claim_id=claim_id,
                    priority="HIGH",
                ))
    return tasks


def role_can_edit_evidence(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST", "CLIENT"}


def role_can_verify_evidence(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST"}
