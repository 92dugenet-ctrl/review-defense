"""Application service for auditable case escalations.

Owns escalation signal materialization and human acknowledgement/resolution
persistence. HTTP authorization and response serialization remain in the API.
"""
from __future__ import annotations
from dataclasses import replace
from typing import Any, Callable
from .escalation_workflow import Escalation, signal_from_sla
from .security_hardening import utc_now

class CaseEscalationService:
    def __init__(self, *, store: Any, repository: Any = None,
                 audit_event: Callable[..., Any] | None = None):
        self.store = store
        self.repository = repository
        self.audit_event = audit_event

    def for_sla(self, *, organization_id: str, case_id: str, sla: Any) -> Escalation | None:
        signal = signal_from_sla(case_id, sla)
        if signal is None:
            return (self.store.escalations.get((organization_id, case_id, "DUE"))
                    or self.store.escalations.get((organization_id, case_id, "CRITICAL")))
        key = (organization_id, case_id, signal.level)
        existing = self.store.escalations.get(key)
        if existing is not None:
            return existing
        if self.repository is not None and hasattr(self.repository, "get_escalation"):
            row = self.repository.get_escalation(organization_id, case_id, signal.level)
            if row:
                signal = Escalation(**row)
        self.store.escalations[key] = signal
        return signal

    def _get(self, *, organization_id: str, case_id: str, level: str) -> Escalation:
        key = (organization_id, case_id, level)
        escalation = self.store.escalations.get(key)
        if escalation is None and self.repository is not None and hasattr(self.repository, "get_escalation"):
            row = self.repository.get_escalation(organization_id, case_id, level)
            if row:
                escalation = Escalation(**row)
                self.store.escalations[key] = escalation
        if escalation is None:
            raise KeyError("escalation not found")
        return escalation

    def acknowledge(self, *, organization_id: str, case_id: str, level: str, user_id: str) -> Escalation:
        escalation = self._get(organization_id=organization_id, case_id=case_id, level=level)
        if escalation.status == "RESOLVED":
            raise ValueError("escalation is already resolved")
        escalation.status = "ACKNOWLEDGED"
        escalation.acknowledged_by = user_id
        escalation.acknowledged_at = utc_now().isoformat()
        if self.repository is not None and hasattr(self.repository, "upsert_escalation"):
            self.repository.upsert_escalation(organization_id, escalation.payload())
        if self.audit_event is not None:
            self.audit_event(organization_id, user_id, "ESCALATION_ACKNOWLEDGED",
                             f"case:{case_id}", level=level)
        return replace(escalation)

    def resolve(self, *, organization_id: str, case_id: str, level: str, user_id: str) -> Escalation:
        escalation = self._get(organization_id=organization_id, case_id=case_id, level=level)
        if escalation.status == "RESOLVED":
            raise ValueError("escalation is already resolved")
        escalation.status = "RESOLVED"
        escalation.resolved_by = user_id
        escalation.resolved_at = utc_now().isoformat()
        if self.repository is not None and hasattr(self.repository, "upsert_escalation"):
            self.repository.upsert_escalation(organization_id, escalation.payload())
        if self.audit_event is not None:
            self.audit_event(organization_id, user_id, "ESCALATION_RESOLVED",
                             f"case:{case_id}", level=level)
        return replace(escalation)
