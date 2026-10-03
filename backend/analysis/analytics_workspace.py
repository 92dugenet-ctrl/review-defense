"""V4.10 Analytics Center.

Descriptive, tenant-scoped operational analytics. No ranking, policy mutation,
or prediction of external outcomes.
"""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CaseMetric:
    organization_id: str
    case_id: str
    status: str
    policy_codes: tuple[str, ...] = ()
    claim_count: int = 0
    evidence_count: int = 0
    evidence_coverage: float = 0.0
    analyst_minutes: int = 0
    submissions: int = 0
    appeals: int = 0
    outcomes: int = 0
    created_at: str = ""


@dataclass(frozen=True)
class Period:
    start: str
    end: str


def _tenant(
    rows: Iterable[CaseMetric],
    organization_id: str,
) -> list[CaseMetric]:
    if not organization_id:
        raise ValueError("organization_id is required")

    return [
        row
        for row in rows
        if row.organization_id == organization_id
    ]


def summarize_cases(
    rows: Iterable[CaseMetric],
    *,
    organization_id: str,
) -> dict[str, int | float]:
    data = _tenant(rows, organization_id)

    return {
        "cases": len(data),
        "claims": sum(row.claim_count for row in data),
        "evidence": sum(row.evidence_count for row in data),
        "submissions": sum(row.submissions for row in data),
        "appeals": sum(row.appeals for row in data),
        "outcomes": sum(row.outcomes for row in data),
        "analyst_minutes": sum(row.analyst_minutes for row in data),
        "avg_evidence_coverage": (
            round(
                sum(row.evidence_coverage for row in data) / len(data),
                2,
            )
            if data
            else 0.0
        ),
    }


def status_breakdown(
    rows: Iterable[CaseMetric],
    *,
    organization_id: str,
) -> dict[str, int]:
    result: dict[str, int] = {}

    for row in _tenant(rows, organization_id):
        result[row.status] = result.get(row.status, 0) + 1

    return result


def policy_breakdown(
    rows: Iterable[CaseMetric],
    *,
    organization_id: str,
) -> dict[str, int]:
    result: dict[str, int] = {}

    for row in _tenant(rows, organization_id):
        for code in row.policy_codes:
            result[code] = result.get(code, 0) + 1

    return result


def compare_periods(
    current: dict[str, int | float],
    previous: dict[str, int | float],
    *,
    keys: tuple[str, ...] = (
        "cases",
        "claims",
        "evidence",
        "submissions",
        "appeals",
        "outcomes",
        "analyst_minutes",
    ),
) -> dict[str, dict[str, int | float]]:
    result: dict[str, dict[str, int | float]] = {}

    for key in keys:
        current_value = current.get(key, 0)
        previous_value = previous.get(key, 0)
        delta = current_value - previous_value
        percent_change = (
            0.0
            if previous_value == 0
            else round((delta / previous_value) * 100, 2)
        )

        result[key] = {
            "current": current_value,
            "previous": previous_value,
            "delta": delta,
            "percent_change": percent_change,
        }

    return result


def average_analyst_minutes(
    rows: Iterable[CaseMetric],
    *,
    organization_id: str,
) -> float:
    data = _tenant(rows, organization_id)

    if not data:
        return 0.0

    return round(
        sum(row.analyst_minutes for row in data) / len(data),
        2,
    )


def coverage_buckets(
    rows: Iterable[CaseMetric],
    *,
    organization_id: str,
) -> dict[str, int]:
    result = {
        "0-49": 0,
        "50-79": 0,
        "80-99": 0,
        "100": 0,
    }

    for row in _tenant(rows, organization_id):
        value = max(0.0, min(100.0, row.evidence_coverage))

        if value >= 100:
            result["100"] += 1
        elif value >= 80:
            result["80-99"] += 1
        elif value >= 50:
            result["50-79"] += 1
        else:
            result["0-49"] += 1

    return result
