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
    @staticmethod
    def hydrate_case(store: Any, repository: Any, organization_id: str, case_id: str) -> Case | None:
        key = (organization_id, case_id)
        case = store.cases.get(key)
        if case is None and repository is not None and hasattr(repository, "get_case_persistent"):
            row = repository.get_case_persistent(organization_id, case_id)
            if row:
                case = CaseService.from_row(row)
                store.cases[key] = case
        return case
    @staticmethod
    def hydrate_context(store: Any, repository: Any, organization_id: str, case_id: str, review_from_row: Any = None) -> tuple[Case | None, Any, list[Any], list[Any]]:
        case = CaseService.hydrate_case(store, repository, organization_id, case_id)
        if case is None:
            return None, None, [], []

        key = (organization_id, case_id)
        if repository is not None and hasattr(repository, "list_evidence"):
            for row in repository.list_evidence(organization_id, case_id) or []:
                # The repository query is tenant- and case-scoped, but validate
                # the returned row as a second boundary before caching it.
                if len(row) < 12 or str(row[1]) != organization_id or str(row[2]) != case_id:
                    continue
                evidence = {
                    "evidence_id": str(row[0]),
                    "organization_id": str(row[1]),
                    "case_id": str(row[2]),
                    "filename": str(row[3]),
                    "content_type": row[4],
                    "size_bytes": int(row[5]) if row[5] is not None else 0,
                    "sha256": str(row[6]),
                    "object_key": str(row[7]),
                    "verified": bool(row[8]),
                    "created_by": row[9],
                    "verified_by": row[10],
                    "verified_at": CaseService._iso_value(row[11]),
                }
                store.evidence[(organization_id, evidence["evidence_id"])] = evidence

        if repository is not None and hasattr(repository, "list_evidence_facts"):
            for row in repository.list_evidence_facts(organization_id, case_id) or []:
                # Facts must belong to the requested case even if an adapter
                # accidentally returns rows outside its query predicate.
                if len(row) < 10 or str(row[2]) != case_id:
                    continue
                fact = {
                    "fact_id": str(row[0]),
                    "evidence_id": str(row[1]),
                    "case_id": str(row[2]),
                    "key": str(row[3]),
                    "kind": str(row[4]),
                    "value": row[5],
                    "source_location": row[6],
                    "verified": bool(row[7]),
                    "verified_by": row[8],
                    "verified_at": CaseService._iso_value(row[9]),
                }
                store.evidence_facts[(organization_id, fact["fact_id"])] = fact

        review = store.reviews.get((organization_id, case.review_id))
        if review is None and repository is not None and hasattr(repository, "get_review"):
            review = repository.get_review(organization_id, case.review_id)
            if review is not None:
                review = review_from_row(review) if review_from_row is not None else review
                store.reviews[(organization_id, case.review_id)] = review

        evidence = [
            value
            for (key, value) in store.evidence.items()
            if key[0] == organization_id
            and isinstance(value, dict)
            and str(value.get("organization_id", organization_id)) == organization_id
            and str(value.get("case_id", "")) == case_id
        ]
        target_evidence_ids = {str(item["evidence_id"]) for item in evidence}
        evidence_facts = []
        for (org_id, _), cached in store.evidence_facts.items():
            if org_id != organization_id:
                continue
            # Older store versions may hold one fact or a list of facts per key.
            records = cached if isinstance(cached, list) else [cached]
            evidence_facts.extend(
                fact for fact in records
                if isinstance(fact, dict)
                and str(fact.get("case_id", "")) == case_id
                and str(fact.get("evidence_id", "")) in target_evidence_ids
            )
        return case, review, evidence, evidence_facts

