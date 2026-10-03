"""V6.18 human disposition of structured contradiction findings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256


ALLOWED = frozenset(
    {
        "CONFIRMED_CONTRADICTION",
        "EXPLAINED",
        "FALSE_POSITIVE",
        "NEEDS_MORE_EVIDENCE",
    }
)


@dataclass(frozen=True)
class ContradictionDisposition:
    disposition_id: str
    organization_id: str
    case_id: str
    contradiction_id: str
    status: str
    rationale: str
    actor_id: str
    created_at: str
    requires_human_review: bool = True


def disposition_id(
    organization_id: str,
    contradiction_id: str,
    actor_id: str,
    created_at: str,
) -> str:
    material = (
        f"{organization_id}|{contradiction_id}|"
        f"{actor_id}|{created_at}"
    )
    digest = sha256(material.encode()).hexdigest()[:24]

    return "disp_" + digest


def validate_disposition(
    status: str,
    rationale: str,
) -> tuple[str, str]:
    normalized_status = str(status or "").upper()
    normalized_rationale = str(rationale or "").strip()

    if normalized_status not in ALLOWED:
        raise ValueError("invalid contradiction disposition")

    if not normalized_rationale:
        raise ValueError("rationale is required")

    if len(normalized_rationale) > 2000:
        raise ValueError("rationale is too long")

    return normalized_status, normalized_rationale


def make_disposition(
    *,
    organization_id: str,
    case_id: str,
    contradiction_id: str,
    status: str,
    rationale: str,
    actor_id: str,
    created_at: str | None = None,
) -> ContradictionDisposition:
    normalized_status, normalized_rationale = validate_disposition(
        status,
        rationale,
    )
    created_at_value = (
        created_at
        or datetime.now(timezone.utc).isoformat()
    )

    return ContradictionDisposition(
        disposition_id(
            organization_id,
            contradiction_id,
            actor_id,
            created_at_value,
        ),
        organization_id,
        case_id,
        contradiction_id,
        normalized_status,
        normalized_rationale,
        actor_id,
        created_at_value,
        True,
    )
