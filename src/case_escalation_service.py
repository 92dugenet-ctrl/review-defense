"""Application service for auditable case escalations.

# Escalades : convertit les indicateurs SLA en alertes suivies, expose une vue organisationnelle et délègue la mise en file des notifications au service dédié. L'accusé de réception et la résolution restent des actions humaines auditées.

Owns escalation signal materialization and human acknowledgement/resolution
persistence. HTTP authorization and response serialization remain in the API.
"""
from __future__ import annotations
from dataclasses import replace
from typing import Any, Callable
from .escalation_workflow import Escalation, signal_from_sla
from .security_hardening import utc_now
from .case_sla_service import CaseSLAService
from .operations_ui import (
    ReviewSummary, ClaimView, PolicySignalView, EvidenceView,
    Contradiction, CaseWorkspace, missing_evidence_tasks,
)
from .review_workspace import extract_claims, classify_policy_signals
from .review_queue import score_case

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

    def list_for_organization(self, *, organization_id: str, calendar: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for (org, case_id), case in self.store.cases.items():
            if org != organization_id:
                continue
            review = self.store.reviews.get((org, case.review_id))
            if review is None:
                continue
            claims = extract_claims(review)
            signals = classify_policy_signals(claims)
            contradictions = self.store.contradictions.get((org, case_id), [])
            suggestions = self.store.fact_suggestions.get((org, case_id), [])
            evidence_rows = [
                e for (eo, _), e in self.store.evidence.items()
                if eo == org and e.get("case_id") == case_id
            ]
            evidence = tuple(
                EvidenceView(
                    e["evidence_id"], e["filename"], e.get("content_type") or "UNKNOWN",
                    e["sha256"], "VERIFIED" if e.get("verified") else "UNVERIFIED",
                )
                for e in evidence_rows
            )
            workspace = CaseWorkspace(
                case_id, org, case.status, "NORMAL",
                ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
                tuple(ClaimView(c.claim_id, c.text, c.claim_type, "UNVERIFIED") for c in claims),
                tuple(PolicySignalView(s.code, s.status, s.justification) for s in signals),
                evidence, (), tuple(
                    Contradiction(
                        c["contradiction_id"], c["description"], c["claim_id"],
                        tuple(c["evidence_ids"]), True,
                    )
                    for c in contradictions
                ),
            )
            missing = missing_evidence_tasks(workspace, {c.claim_id: [] for c in claims})
            queue_item = score_case(
                case_id=case_id,
                created_at=case.created_at,
                policy_statuses=[s.status for s in signals],
                contradiction_count=len(contradictions),
                missing_evidence_count=len(missing),
                unverified_suggestion_count=sum(1 for x in suggestions if not x.get("verified")),
                assigned_to=case.assigned_to,
            )
            sla = CaseSLAService(repository=self.repository).calculate(case, queue_item.priority, calendar)
            escalation = self.for_sla(
                organization_id=organization_id, case_id=case_id, sla=sla,
            )
            if escalation:
                remaining_seconds = (
                    round((sla.remaining_hours or 0.0) * 3600, 2)
                    if sla.remaining_hours is not None else None
                )
                items.append(
                    escalation.payload()
                    | {"sla": {
                        "case_id": case_id,
                        "priority": queue_item.priority,
                        "remaining_seconds": remaining_seconds,
                        "breached": sla.status == "OVERDUE",
                        "escalation": sla.escalation,
                    }, "assigned_to": case.assigned_to}
                )
        return items

    def queue_notification(self, *, notifications: Any, organization_id: str,
                            case_id: str, level: str, channel: str, target: str,
                            subject: str, body: str, actor_id: str) -> tuple[Any, bool]:
        escalation = self._get(
            organization_id=organization_id, case_id=case_id, level=level,
        )
        if escalation.status == "RESOLVED":
            raise ValueError("resolved escalation cannot be notified")
        return notifications.queue(
            organization_id=organization_id,
            case_id=case_id,
            level=level,
            channel=channel,
            target=target,
            subject=subject,
            body=body,
            actor_id=actor_id,
        )

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
