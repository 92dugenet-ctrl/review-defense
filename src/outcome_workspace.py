"""V4.8 Outcome & Appeal Tracking Workspace.

Records externally observed outcomes without inferring Google's reasons or
performing any external action. Outcomes are tenant-bound and auditable.
"""
from dataclasses import dataclass
from typing import Literal

OutcomeKind = Literal[
    "REMOVED", "REJECTED", "NO_RESPONSE", "APPEAL_AVAILABLE",
    "APPEAL_REJECTED", "APPEALED", "CLOSED", "UNKNOWN"
]

RECORDER_ROLES = {"OWNER", "ADMIN", "ANALYST"}

@dataclass(frozen=True)
class OutcomeRecord:
    outcome_id: str
    organization_id: str
    submission_id: str
    case_id: str
    kind: OutcomeKind
    recorded_at: str
    recorded_by: str
    source: str
    reason: str | None = None
    external_reference: str | None = None
    notes: str | None = None

@dataclass(frozen=True)
class OutcomeWorkspace:
    organization_id: str
    submission_id: str
    outcomes: tuple[OutcomeRecord, ...] = ()


def record_outcome(*, outcome_id: str, organization_id: str, submission_id: str,
                   case_id: str, kind: OutcomeKind, recorded_at: str,
                   recorded_by: str, source: str, reason: str | None = None,
                   external_reference: str | None = None,
                   notes: str | None = None) -> OutcomeRecord:
    required = (outcome_id, organization_id, submission_id, case_id, recorded_by, source)
    if not all(required):
        raise ValueError("outcome identity fields are required")
    allowed = {"REMOVED", "REJECTED", "NO_RESPONSE", "APPEAL_AVAILABLE",
               "APPEAL_REJECTED", "APPEALED", "CLOSED", "UNKNOWN"}
    if kind not in allowed:
        raise ValueError("unsupported outcome kind")
    if reason is not None and not reason.strip():
        raise ValueError("reason must be non-empty when provided")
    return OutcomeRecord(outcome_id, organization_id, submission_id, case_id,
                         kind, recorded_at, recorded_by, source, reason,
                         external_reference, notes)


def can_record_outcome(role: str) -> bool:
    return role in RECORDER_ROLES


def can_close_outcome(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST"}


def outcome_requires_appeal(kind: OutcomeKind) -> bool:
    return kind in {"REJECTED", "APPEAL_AVAILABLE"}


def outcome_is_final(kind: OutcomeKind) -> bool:
    return kind in {"REMOVED", "APPEAL_REJECTED", "CLOSED"}


def summarize_outcomes(outcomes: tuple[OutcomeRecord, ...] | list[OutcomeRecord]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for outcome in outcomes:
        summary[outcome.kind] = summary.get(outcome.kind, 0) + 1
    return summary
