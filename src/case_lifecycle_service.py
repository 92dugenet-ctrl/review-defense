"""Cases lifecycle application service.

Owns case creation and organization-scoped case listing. HTTP validation,
authorization, response formatting and routing remain outside this module.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Any, Callable

from .case_service import Case
from .security_hardening import utc_now


class CaseLifecycleService:
    def __init__(self, *, store: Any, repository: Any = None,
                 audit_event: Callable[..., Any] | None = None):
        self.store = store
        self.repository = repository
        self.audit_event = audit_event

    def create(self, *, organization_id: str, review_id: str, actor_id: str) -> Case:
        case_id = str(uuid.uuid4())
        case = Case(
            case_id,
            organization_id,
            review_id,
            "ANALYZING",
            created_at=utc_now().isoformat(),
        )
        self.store.cases[(organization_id, case_id)] = case
        if self.repository is not None:
            self.repository.create_case_persistent(
                organization_id, case_id, review_id, case.status, actor_id
            )
        if self.audit_event is not None:
            self.audit_event(
                organization_id,
                actor_id,
                "CASE_CREATED",
                f"case:{case_id}",
                review_id=review_id,
            )
        return case

    def list_for_organization(self, *, organization_id: str) -> list[Case]:
        if self.repository is not None and hasattr(self.repository, "list_cases"):
            for row in self.repository.list_cases(organization_id):
                case_id = str(row[0])
                key = (organization_id, case_id)
                if key not in self.store.cases:
                    self.store.cases[key] = CaseService.from_row(row)
        return [
            case
            for (org, _), case in self.store.cases.items()
            if org == organization_id
        ]


# Import kept local to avoid making the lifecycle module responsible for the
# Case contract definition while preserving the existing hydration seam.
from .case_service import CaseService
