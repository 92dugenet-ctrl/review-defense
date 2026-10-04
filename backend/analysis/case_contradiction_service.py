"""Cases contradiction application seam.

Owns contradiction analysis and human disposition persistence side effects.
"""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
from typing import Any, Callable, Iterable
from .contradiction_engine import EvidenceFact, detect_contradictions
from .contradiction_disposition import make_disposition
from ..authentication.security_hardening import utc_now

class CaseContradictionService:
    def __init__(self, *, repository: Any = None, audit_event: Callable[..., Any] | None = None,
                 contradiction_store: Any = None, disposition_store: Any = None,
                 disposition_history_store: Any = None):
        self.repository = repository
        self.audit_event = audit_event
        self.contradiction_store = contradiction_store
        self.disposition_store = disposition_store
        self.disposition_history_store = disposition_history_store

    def analyze(self, *, organization_id: str, case_id: str, user_id: str,
                claims: Iterable[Any], evidence_facts: Iterable[EvidenceFact],
                evidence_ids: list[str]) -> list[dict[str, Any]]:
        rows = [asdict(f) for f in detect_contradictions(
            organization_id=organization_id, case_id=case_id,
            claims=claims, evidence_facts=evidence_facts)]
        if self.contradiction_store is not None:
            self.contradiction_store[(organization_id, case_id)] = rows
        if self.repository is not None:
            for finding in rows:
                self.repository.put_contradiction(organization_id, finding)
        if self.audit_event is not None:
            self.audit_event(organization_id, user_id, "CONTRADICTIONS_ANALYZED",
                             f"case:{case_id}", contradiction_count=len(rows),
                             evidence_ids=evidence_ids)
        return rows

    def disposition(self, *, organization_id: str, case_id: str,
                    contradiction_id: str, status: str, rationale: str,
                    actor_id: str, created_at: str | None = None) -> dict[str, Any]:
        disp = make_disposition(
            organization_id=organization_id, case_id=case_id,
            contradiction_id=contradiction_id, status=status,
            rationale=rationale, actor_id=actor_id,
            created_at=created_at or utc_now().isoformat())
        data = asdict(disp)
        history = dict(data)
        history["history_id"] = "hist_" + sha256(
            f"{data['disposition_id']}|{data['created_at']}".encode()).hexdigest()[:24]
        if self.disposition_store is not None:
            self.disposition_store[(organization_id, contradiction_id)] = data
        if self.disposition_history_store is not None:
            self.disposition_history_store.setdefault((organization_id, contradiction_id), []).append(history)
        if self.repository is not None and hasattr(self.repository, "upsert_contradiction_disposition"):
            self.repository.upsert_contradiction_disposition(organization_id, data)
        if self.repository is not None and hasattr(self.repository, "append_contradiction_disposition_history"):
            self.repository.append_contradiction_disposition_history(organization_id, history)
        if self.audit_event is not None:
            self.audit_event(organization_id, actor_id, "CONTRADICTION_DISPOSITIONED",
                             f"case:{case_id}", contradiction_id=contradiction_id,
                             status=disp.status)
        return data
