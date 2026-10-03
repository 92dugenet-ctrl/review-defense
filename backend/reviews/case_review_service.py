"""Cases review checklist application seam.

Owns checklist hydration, creation, readiness assessment and checklist-item
persistence.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable

from .case_review import (
    ReviewChecklistItem,
    assess_readiness,
    build_checklist,
)
from .security_hardening import utc_now


class CaseReviewService:
    def __init__(
        self,
        *,
        store: Any,
        repository: Any = None,
        audit_event: Callable[..., Any] | None = None,
    ):
        self.store = store
        self.repository = repository
        self.audit_event = audit_event

    def ensure_checklist(
        self,
        *,
        organization_id: str,
        case_id: str,
        has_policy_signals: bool,
        contradiction_count: int,
        unverified_fact_count: int,
        missing_evidence_count: int,
    ):
        key = (organization_id, case_id)
        can_load_checklist = (
            self.repository is not None
            and hasattr(
                self.repository,
                "list_case_review_checklist",
            )
        )

        if key not in self.store.review_checklists and can_load_checklist:
            rows = self.repository.list_case_review_checklist(
                organization_id,
                case_id,
            )
            columns = (
                "item_id",
                "organization_id",
                "case_id",
                "code",
                "label",
                "required",
                "completed",
                "completed_by",
                "completed_at",
                "note",
            )
            self.store.review_checklists[key] = [
                dict(zip(columns, row))
                for row in rows
            ]

        if key not in self.store.review_checklists:
            checklist = build_checklist(
                organization_id=organization_id,
                case_id=case_id,
                has_policy_signals=has_policy_signals,
                contradiction_count=contradiction_count,
                unverified_fact_count=unverified_fact_count,
                missing_evidence_count=missing_evidence_count,
            )
            self.store.review_checklists[key] = [
                asdict(item)
                for item in checklist
            ]

            can_save_checklist = (
                self.repository is not None
                and hasattr(
                    self.repository,
                    "upsert_case_review_checklist",
                )
            )

            if can_save_checklist:
                for item in self.store.review_checklists[key]:
                    self.repository.upsert_case_review_checklist(
                        organization_id,
                        item,
                    )

        return self.store.review_checklists[key]

    def update_item(
        self,
        *,
        organization_id: str,
        case_id: str,
        code: str,
        completed: bool,
        user_id: str,
        note: str | None = None,
    ):
        checklist = self.store.review_checklists[
            (organization_id, case_id)
        ]
        row = next(
            (
                item
                for item in checklist
                if item["code"] == code
            ),
            None,
        )

        if row is None:
            raise KeyError("checklist item not found")

        row["completed"] = completed
        row["completed_by"] = (
            user_id
            if completed
            else None
        )
        row["completed_at"] = (
            utc_now().isoformat()
            if completed
            else None
        )
        row["note"] = (
            str(note)[:1000]
            if note is not None
            else None
        )

        can_save_checklist_item = (
            self.repository is not None
            and hasattr(
                self.repository,
                "upsert_case_review_checklist",
            )
        )

        if can_save_checklist_item:
            self.repository.upsert_case_review_checklist(
                organization_id,
                row,
            )

        if self.audit_event is not None:
            self.audit_event(
                organization_id,
                user_id,
                "CASE_REVIEW_CHECKLIST_UPDATED",
                f"case:{case_id}",
                code=code,
                completed=completed,
            )

        return row

    def readiness(
        self,
        *,
        case_id: str,
        organization_id: str,
        items,
        contradiction_count: int,
        unverified_fact_count: int,
        missing_evidence_count: int,
    ):
        review_items = [
            ReviewChecklistItem(**item)
            for item in items
        ]

        return assess_readiness(
            case_id=case_id,
            organization_id=organization_id,
            items=review_items,
            contradiction_count=contradiction_count,
            unverified_fact_count=unverified_fact_count,
            missing_evidence_count=missing_evidence_count,
        )
