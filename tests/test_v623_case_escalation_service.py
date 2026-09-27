import pytest
from src.api_server import MemoryStore
from src.case_escalation_service import CaseEscalationService
from src.escalation_workflow import Escalation

class Repository:
    def __init__(self): self.calls = []
    def get_escalation(self, organization_id, case_id, level):
        self.calls.append(("get", organization_id, case_id, level)); return None
    def upsert_escalation(self, organization_id, payload):
        self.calls.append(("upsert", organization_id, payload["status"]))

class SLA:
    escalation = "DUE"

def test_signal_materialization_is_tenant_scoped_and_persistable():
    store, repo = MemoryStore(), Repository()
    service = CaseEscalationService(store=store, repository=repo, audit_event=store.audit_event)
    escalation = service.for_sla(organization_id="org-a", case_id="c1", sla=SLA())
    assert escalation.level == "DUE"
    assert store.escalations[("org-a", "c1", "DUE")] is escalation
    assert repo.calls == [("get", "org-a", "c1", "DUE")]

def test_acknowledge_and_resolve_are_audited_and_persisted():
    store, repo = MemoryStore(), Repository()
    store.escalations[("org-a", "c1", "DUE")] = Escalation("c1", "DUE", "SLA breached")
    service = CaseEscalationService(store=store, repository=repo, audit_event=store.audit_event)
    acknowledged = service.acknowledge(organization_id="org-a", case_id="c1", level="DUE", user_id="u1")
    resolved = service.resolve(organization_id="org-a", case_id="c1", level="DUE", user_id="u2")
    assert acknowledged.status == "ACKNOWLEDGED"
    assert resolved.status == "RESOLVED"
    assert [x["action"] for x in store.audit] == ["ESCALATION_ACKNOWLEDGED", "ESCALATION_RESOLVED"]
    assert [x[0] for x in repo.calls] == ["upsert", "upsert"]

def test_resolved_escalation_cannot_be_acknowledged_or_resolved_again():
    store = MemoryStore()
    store.escalations[("org-a", "c1", "DUE")] = Escalation("c1", "DUE", "SLA breached", status="RESOLVED")
    service = CaseEscalationService(store=store)
    with pytest.raises(ValueError, match="already resolved"):
        service.acknowledge(organization_id="org-a", case_id="c1", level="DUE", user_id="u1")
    with pytest.raises(ValueError, match="already resolved"):
        service.resolve(organization_id="org-a", case_id="c1", level="DUE", user_id="u1")
