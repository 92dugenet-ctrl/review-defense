"""V6.18 human disposition of structured contradiction findings."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256

ALLOWED = frozenset({"CONFIRMED_CONTRADICTION", "EXPLAINED", "FALSE_POSITIVE", "NEEDS_MORE_EVIDENCE"})

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

def disposition_id(organization_id: str, contradiction_id: str, actor_id: str, created_at: str) -> str:
    return "disp_" + sha256(f"{organization_id}|{contradiction_id}|{actor_id}|{created_at}".encode()).hexdigest()[:24]

def validate_disposition(status: str, rationale: str) -> tuple[str, str]:
    status = str(status or "").upper()
    rationale = str(rationale or "").strip()
    if status not in ALLOWED:
        raise ValueError("invalid contradiction disposition")
    if not rationale:
        raise ValueError("rationale is required")
    if len(rationale) > 2000:
        raise ValueError("rationale is too long")
    return status, rationale

def make_disposition(*, organization_id: str, case_id: str, contradiction_id: str, status: str, rationale: str, actor_id: str, created_at: str | None = None) -> ContradictionDisposition:
    status, rationale = validate_disposition(status, rationale)
    at = created_at or datetime.now(timezone.utc).isoformat()
    return ContradictionDisposition(disposition_id(organization_id, contradiction_id, actor_id, at), organization_id, case_id, contradiction_id, status, rationale, actor_id, at, True)
