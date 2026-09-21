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

def _tenant(rows: Iterable[CaseMetric], organization_id: str) -> list[CaseMetric]:
    if not organization_id:
        raise ValueError("organization_id is required")
    return [r for r in rows if r.organization_id == organization_id]

def summarize_cases(rows: Iterable[CaseMetric], *, organization_id: str) -> dict[str, int | float]:
    data = _tenant(rows, organization_id)
    return {
        "cases": len(data),
        "claims": sum(r.claim_count for r in data),
        "evidence": sum(r.evidence_count for r in data),
        "submissions": sum(r.submissions for r in data),
        "appeals": sum(r.appeals for r in data),
        "outcomes": sum(r.outcomes for r in data),
        "analyst_minutes": sum(r.analyst_minutes for r in data),
        "avg_evidence_coverage": round(sum(r.evidence_coverage for r in data) / len(data), 2) if data else 0.0,
    }

def status_breakdown(rows: Iterable[CaseMetric], *, organization_id: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in _tenant(rows, organization_id):
        result[row.status] = result.get(row.status, 0) + 1
    return result

def policy_breakdown(rows: Iterable[CaseMetric], *, organization_id: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in _tenant(rows, organization_id):
        for code in row.policy_codes:
            result[code] = result.get(code, 0) + 1
    return result

def compare_periods(current: dict[str, int | float], previous: dict[str, int | float], *, keys: tuple[str, ...] = ("cases", "claims", "evidence", "submissions", "appeals", "outcomes", "analyst_minutes")) -> dict[str, dict[str, int | float]]:
    result: dict[str, dict[str, int | float]] = {}
    for key in keys:
        cur = current.get(key, 0)
        prev = previous.get(key, 0)
        delta = cur - prev
        pct = 0.0 if prev == 0 else round((delta / prev) * 100, 2)
        result[key] = {"current": cur, "previous": prev, "delta": delta, "percent_change": pct}
    return result

def average_analyst_minutes(rows: Iterable[CaseMetric], *, organization_id: str) -> float:
    data = _tenant(rows, organization_id)
    return round(sum(r.analyst_minutes for r in data) / len(data), 2) if data else 0.0

def coverage_buckets(rows: Iterable[CaseMetric], *, organization_id: str) -> dict[str, int]:
    result = {"0-49": 0, "50-79": 0, "80-99": 0, "100": 0}
    for row in _tenant(rows, organization_id):
        value = max(0.0, min(100.0, row.evidence_coverage))
        if value >= 100: result["100"] += 1
        elif value >= 80: result["80-99"] += 1
        elif value >= 50: result["50-79"] += 1
        else: result["0-49"] += 1
    return result
