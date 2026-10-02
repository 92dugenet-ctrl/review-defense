import pytest

from src.api_server import MemoryStore
from src.case_service import Case
from src.case_decision_service import CaseDecisionService
from src.review_workspace import ReviewContext


class RecordingRepository:
    def __init__(self):
        self.calls = []

    def put_decision(self, organization_id, decision):
        self.calls.append(("put_decision", organization_id, decision["status"]))

    def update_case(self, organization_id, case_id, **kwargs):
        self.calls.append(("update_case", organization_id, case_id, kwargs))

    def put_snapshot(self, organization_id, case_id, sha256, payload, frozen_by, frozen_at):
        self.calls.append(("put_snapshot", organization_id, case_id, sha256))

    def put_approval(self, organization_id, approval):
        self.calls.append(("put_approval", organization_id, approval["approval_id"]))


def make_service():
    store = MemoryStore()
    repo = RecordingRepository()
    service = CaseDecisionService(store=store, repository=repo, audit_event=store.audit_event)
    return service, store, repo


def make_case(store):
    case = Case(
        case_id="c1",
        organization_id="org-a",
        review_id="r1",
        status="ANALYZING",
        created_at="2026-09-20T12:00:00Z",
    )
    review = ReviewContext(
        review_id="r1",
        organization_id="org-a",
        location_id="loc-1",
        author_display_name="Author",
        rating=1,
        text="Excellent mais facture 60 euros.",
        published_at="2026-09-20T11:00:00Z",
    )
    store.cases[("org-a", "c1")] = case
    store.reviews[("org-a", "r1")] = review
    return case


def test_create_persists_and_links_case():
    service, store, repo = make_service()
    case = make_case(store)

    decision = service.create(
        case=case,
        user_id="u1",
        kind="HUMAN_REVIEW",
        rationale="Review the evidence before any action.",
    )

    assert decision.status == "DRAFT"
    assert case.decision_id == decision.decision_id
    assert case.status == "ANALYZED"
    assert ("org-a", decision.decision_id) in store.decisions
    assert repo.calls[0][0] == "put_decision"
    assert any(e["action"] == "DECISION_CREATED" for e in store.audit)


def test_freeze_canonicalizes_and_requests_approval():
    service, store, repo = make_service()
    case = make_case(store)
    decision = service.create(
        case=case,
        user_id="u1",
        kind="HUMAN_REVIEW",
        rationale="Review the evidence before any action.",
    )

    frozen, snapshot = service.freeze(case=case, user_id="u1")

    assert frozen.decision_id == decision.decision_id
    assert frozen.status == "PENDING_APPROVAL"
    assert case.status == "HUMAN_REVIEW"
    assert case.snapshot_sha256 == snapshot.sha256
    assert store.snapshots[("org-a", "c1")] == snapshot
    assert any(c[0] == "put_snapshot" for c in repo.calls)
    assert any(e["action"] == "DOSSIER_FROZEN" for e in store.audit)


def test_approval_persists_and_requires_exact_frozen_snapshot():
    service, store, repo = make_service()
    case = make_case(store)
    service.create(
        case=case,
        user_id="u1",
        kind="HUMAN_REVIEW",
        rationale="Review the evidence before any action.",
    )
    service.freeze(case=case, user_id="u1")

    with pytest.raises(PermissionError):
        service.approve(case=case, user_id="client", user_role="CLIENT")

    approved, event = service.approve(case=case, user_id="admin", user_role="ADMIN")

    assert approved.status == "APPROVED"
    assert event.snapshot_sha256 == case.snapshot_sha256
    assert case.status == "READY_TO_SUBMIT"
    assert any(c[0] == "put_approval" for c in repo.calls)
    assert any(e["action"] == "DECISION_APPROVED" for e in store.audit)
