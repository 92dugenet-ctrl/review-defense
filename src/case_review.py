"""V6.17 Advanced Case Review: explicit analyst checklist and readiness.

This module is deliberately advisory. It can report readiness, but it never
creates/approves/freezes/submits a decision and never calls Google.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
from typing import Iterable

@dataclass(frozen=True)
class ReviewChecklistItem:
    item_id: str
    case_id: str
    organization_id: str
    code: str
    label: str
    required: bool = True
    completed: bool = False
    completed_by: str | None = None
    completed_at: str | None = None
    note: str | None = None

@dataclass(frozen=True)
class ReviewReadiness:
    case_id: str
    organization_id: str
    ready: bool
    required_total: int
    required_completed: int
    open_item_ids: tuple[str, ...]
    contradiction_count: int
    unverified_fact_count: int
    missing_evidence_count: int
    human_review_required: bool = True

def checklist_id(organization_id: str, case_id: str, code: str) -> str:
    return "chk_" + sha256(f"{organization_id}|{case_id}|{code}".encode()).hexdigest()[:24]

def build_checklist(*, organization_id: str, case_id: str, has_policy_signals: bool,
                    contradiction_count: int, unverified_fact_count: int,
                    missing_evidence_count: int) -> tuple[ReviewChecklistItem, ...]:
    specs = [
        ("REVIEW_CONTEXT", "Review context and claims reviewed"),
        ("EVIDENCE_INTEGRITY", "Evidence integrity verified"),
    ]
    if has_policy_signals:
        specs.append(("POLICY_SIGNALS", "Policy signals reviewed"))
    if missing_evidence_count:
        specs.append(("MISSING_EVIDENCE", "Required evidence gaps reviewed"))
    if unverified_fact_count:
        specs.append(("FACT_VERIFICATION", "Extracted fact suggestions reviewed"))
    if contradiction_count:
        specs.append(("CONTRADICTIONS", "Contradictions reviewed and dispositioned"))
    specs.append(("DECISION_RATIONALE", "Human decision rationale prepared or explicitly deferred"))
    return tuple(ReviewChecklistItem(checklist_id(organization_id, case_id, code), case_id, organization_id, code, label) for code, label in specs)

def assess_readiness(*, case_id: str, organization_id: str, items: Iterable[ReviewChecklistItem],
                     contradiction_count: int, unverified_fact_count: int,
                     missing_evidence_count: int) -> ReviewReadiness:
    rows = tuple(items)
    required = tuple(x for x in rows if x.required)
    open_ids = tuple(x.item_id for x in required if not x.completed)
    return ReviewReadiness(case_id, organization_id, not open_ids, len(required), len(required)-len(open_ids), open_ids,
                           contradiction_count, unverified_fact_count, missing_evidence_count, True)
