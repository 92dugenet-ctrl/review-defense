import pytest
from datetime import datetime, timezone
from src.api_server import MemoryStore
from src.case_operations_service import CaseOperationsService
from src.case_service import Case


class Calendar:
    def business_seconds_between(self, start, end):
        return 90.0


class Repository:
    def __init__(self):
        self.calls = []

    def assign_case(self, org, case_id, user_id):
        self.calls.append(("assign", org, case_id, user_id))

    def update_case_sla(self, org, case_id, **kwargs):
        self.calls.append(("sla", org, case_id, kwargs))


def make_case():
    return Case("c1", "org-a", "r1", "ANALYZING", "2026-09-20T12:00:00Z")


def test_assignment_and_sla_controls_persist_and_audit():
    store = MemoryStore()
    repo = Repository()
    service = CaseOperationsService(store=store, repository=repo, audit_event=store.audit_event)
    case = make_case()
    service.assign(case=case, user_id="u1")
    service.unassign(case=case, user_id="u1")
    service.pause_sla(case=case, user_id="u1", reason="waiting", paused_at="2026-09-28T00:00:00+00:00")
    seconds = service.resume_sla(case=case, user_id="u1", calendar=Calendar(), now=datetime.now(timezone.utc))
    assert case.assigned_to is None and seconds == 90.0
    assert any(x[0] == "assign" for x in repo.calls)
    assert any(x[0] == "sla" for x in repo.calls)
    assert {e["action"] for e in store.audit} >= {"CASE_ASSIGNED", "CASE_UNASSIGNED", "CASE_SLA_PAUSED", "CASE_SLA_RESUMED"}


def test_sla_pause_rejects_duplicate_pause():
    service = CaseOperationsService(store=MemoryStore())
    case = make_case()
    case.sla_paused_at = "2026-09-28T00:00:00+00:00"
    with pytest.raises(ValueError, match="already paused"):
        service.pause_sla(case=case, user_id="u1", reason="x", paused_at="now")
