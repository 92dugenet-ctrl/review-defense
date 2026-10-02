"""V6.7 deterministic analyst review queue and priority scoring."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass(frozen=True)
class QueueItem:
    case_id: str
    priority_score: int
    priority: str
    reasons: tuple[str, ...]
    requires_human_review: bool
    assigned_to: str | None = None
    age_hours: float = 0.0


def _age_hours(created_at: str | None, now: datetime) -> float:
    if not created_at:
        return 0.0
    try:
        value = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return max(0.0, (now - value.astimezone(timezone.utc)).total_seconds() / 3600)
    except ValueError:
        return 0.0


def score_case(*, case_id: str, created_at: str | None, policy_statuses: list[str],
               contradiction_count: int, missing_evidence_count: int,
               unverified_suggestion_count: int, assigned_to: str | None = None,
               now: datetime | None = None) -> QueueItem:
    now = now or datetime.now(timezone.utc)
    age = _age_hours(created_at, now)
    score = 0
    reasons: list[str] = []
    strong = sum(s in {"STRONG", "RELEVANT"} for s in policy_statuses)
    possible = sum(s == "POSSIBLE" for s in policy_statuses)
    if strong:
        score += 35; reasons.append(f"{strong} strong/relevant policy signal(s)")
    if possible:
        score += 10; reasons.append(f"{possible} possible policy signal(s)")
    if contradiction_count:
        score += min(35, contradiction_count * 20); reasons.append(f"{contradiction_count} contradiction(s)")
    if missing_evidence_count:
        score += min(20, missing_evidence_count * 5); reasons.append(f"{missing_evidence_count} missing evidence task(s)")
    if unverified_suggestion_count:
        score += min(10, unverified_suggestion_count * 2); reasons.append(f"{unverified_suggestion_count} unverified fact suggestion(s)")
    if age >= 24:
        score += min(20, int(age // 24) * 5); reasons.append(f"{int(age)}h old")
    priority = "CRITICAL" if score >= 80 else "HIGH" if score >= 50 else "NORMAL" if score >= 20 else "LOW"
    return QueueItem(case_id, min(score, 100), priority, tuple(reasons), bool(reasons), assigned_to, round(age, 2))


def sort_queue(items: list[QueueItem]) -> list[QueueItem]:
    return sorted(items, key=lambda x: (-x.priority_score, x.assigned_to is not None, x.case_id))
