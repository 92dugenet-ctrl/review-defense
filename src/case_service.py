"""V1 Cases application seam for case identity and persistence hydration.

This module owns the Case record and the translation from the existing
repository row into the runtime Case contract. It deliberately does not
perform authorization, HTTP handling, business transitions, or persistence
writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Case:
    case_id: str
    organization_id: str
    review_id: str
    status: str = "NEW"
    decision_id: str | None = None
    snapshot_sha256: str | None = None
    assigned_to: str | None = None
    created_at: str | None = None
    sla_paused_at: str | None = None
    sla_paused_seconds: float = 0.0
    sla_pause_reason: str | None = None


class CaseService:
    """First Cases seam: explicit case contract and persistence hydration."""

    @staticmethod
    def from_row(row: Any) -> Case:
        return Case(
            case_id=str(row[0]),
            organization_id=str(row[1]),
            review_id=str(row[2]),
            status=str(row[3]),
            decision_id=str(row[4]) if row[4] is not None else None,
            snapshot_sha256=str(row[5]) if row[5] is not None else None,
            created_at=CaseService._iso_value(row[6]),
        )

    @staticmethod
    def _iso_value(value: Any) -> str | None:
        if value is None:
            return None
        return value.isoformat() if hasattr(value, "isoformat") else str(value)
