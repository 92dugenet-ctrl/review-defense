import pytest

from src.api_server import MemoryStore
from src.case_service import Case
from src.case_decision_service import CaseDecisionService
from src.case_submission_service import CaseSubmissionService
from src.review_workspace import ReviewContext


class RecordingRepository:
    def __init__(self):
        self.calls = []

    def put_decision(self, organization_id, decision):
        self.calls.append(("put_decision", organization_id, decision["status"]))

    def put_submission(self, organization_id, submission):
        self.calls.append(("put_submission", organization_id, submission["submission_id"]))

    def update_case(self, organization_id, case_id, **kwargs):
        self.calls.append(("update_case", organization_id, case_id, kwargs))

    def put_snapshot(self, *args, **kwargs):
        pass

    def put_approval(self, *args, **kwargs):
        pass


def make_case(store):
    case = Case(
        case_id="c1",
        organization_id="org-a",
        review_id="r1",
        status="READY_TO_SUBMIT",
        created_at="2026-09-20T12:00:00Z",
        decision_id="d1",
    )
    store.cases[("org-a", "c1")] = case
    store.decisions[("org-a", "d1")] = type("Decision", (), {"status": "APPROVED"})()
    store.reviews[("org-a", "r1")] = ReviewContext(
        review_id="r1",
        organization_id="org-a",
        location_id="loc-1",
        author_display_name="Author",
        rating=1,
        text="Review",
        published_at="2026-09-20T11:00:00Z",
    )
    return case


def test_prepare_creates_draft_without_external_call():
    store = MemoryStore()
    repo = RecordingRepository()
    service = CaseSubmissionService(store=store, repository=repo, audit_event=store.audit_event)
    case = make_case(store)

    row = service.prepare(case=case, user_id="u1")

    assert row["status"] == "DRAFT"
    assert row["external_call"] is False
    assert store.submissions[("org-a", row["submission_id"])] == row
    assert any(c[0] == "put_submission" for c in repo.calls)
    assert any(e["action"] == "SUBMISSION_PREPARED" for e in store.audit)


def test_prepare_requires_explicit_approval():
    store = MemoryStore()
    service = CaseSubmissionService(store=store)
    case = make_case(store)
    store.decisions[("org-a", "d1")].status = "PENDING_APPROVAL"

    with pytest.raises(ValueError, match="approval"):
        service.prepare(case=case, user_id="u1")
