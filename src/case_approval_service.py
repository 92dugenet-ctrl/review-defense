"""Application service for decision approval reads.

Keeps approval persistence/hydration out of HTTP routing while preserving the
existing approval response contract.
"""
from __future__ import annotations
from dataclasses import asdict
from typing import Any


class CaseApprovalService:
    def __init__(self, *, store: Any, repository: Any = None):
        self.store = store
        self.repository = repository

    def list_for_organization(self, *, organization_id: str) -> list[dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        if self.repository is not None and hasattr(self.repository, "list_approvals"):
            for row in self.repository.list_approvals(organization_id):
                rows[str(row["approval_id"])] = dict(row)
        for event in self.store.approvals:
            if event.organization_id == organization_id:
                rows[str(event.approval_id)] = asdict(event)
        return list(rows.values())
