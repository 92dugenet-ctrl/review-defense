"""Cases submission preparation application seam.

Creates the local submission record after explicit decision approval.
This module never performs an external submission.
"""
from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4


class CaseSubmissionService:
    def __init__(self, *, store: Any, repository: Any = None,
                 audit_event: Callable[..., Any] | None = None):
        self.store = store
        self.repository = repository
        self.audit_event = audit_event

    def prepare(self, *, case: Any, user_id: str) -> dict[str, Any]:
        if not case.decision_id:
            raise ValueError("decision required")
        decision = self.store.decisions[(case.organization_id, case.decision_id)]
        if decision.status != "APPROVED":
            raise ValueError("explicit human approval required before submission")
        submission_id = str(uuid4())
        row = {
            "submission_id": submission_id,
            "case_id": case.case_id,
            "organization_id": case.organization_id,
            "status": "DRAFT",
            "external_call": False,
        }
        self.store.submissions[(case.organization_id, submission_id)] = row
        if self.repository is not None:
            self.repository.put_submission(case.organization_id, row)
        if self.audit_event is not None:
            self.audit_event(
                case.organization_id,
                user_id,
                "SUBMISSION_PREPARED",
                f"submission:{submission_id}",
            )
        return row
