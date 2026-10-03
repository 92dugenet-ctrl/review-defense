from src.api_server import MemoryStore
from src.case_service import Case, CaseService
from src.review_workspace import ReviewContext


class LeakyRepository:
    """Simulates a persistence adapter accidentally returning adjacent rows."""

    def list_evidence(self, organization_id, case_id):
        assert (organization_id, case_id) == ("org-a", "case-1")
        return [
            ("e1", "org-a", "case-1", "one.txt", "text/plain", 1, "sha1", "obj1", True, None, None, None),
            ("e2", "org-a", "case-2", "two.txt", "text/plain", 1, "sha2", "obj2", True, None, None, None),
            ("e3", "org-b", "case-1", "other.txt", "text/plain", 1, "sha3", "obj3", True, None, None, None),
        ]

    def list_evidence_facts(self, organization_id, case_id):
        assert (organization_id, case_id) == ("org-a", "case-1")
        return [
            ("f1", "e1", "case-1", "amount", "text", "10", "", False, None, None),
            ("f2", "e2", "case-2", "amount", "text", "20", "", False, None, None),
            ("f3", "e3", "case-1", "amount", "text", "30", "", False, None, None),
        ]


def test_hydrate_context_returns_only_requested_case_and_tenant_data():
    store = MemoryStore()
    case = Case("case-1", "org-a", "review-1", "ANALYZING")
    store.cases[("org-a", "case-1")] = case
    store.reviews[("org-a", "review-1")] = ReviewContext(
        "review-1", "org-a", "loc", "Author", 1, "Review", "2026-10-03T10:00:00Z"
    )
    # Pre-existing cache entries must not leak adjacent cases or tenants.
    store.evidence[("org-a", "cached-e2")] = {
        "evidence_id": "cached-e2", "organization_id": "org-a", "case_id": "case-2"
    }
    store.evidence[("org-b", "cached-e3")] = {
        "evidence_id": "cached-e3", "organization_id": "org-b", "case_id": "case-1"
    }
    store.evidence_facts[("org-a", "cached-f2")] = {
        "fact_id": "cached-f2", "case_id": "case-2"
    }
    store.evidence_facts[("org-a", "cached-f1")] = [
        {"fact_id": "cached-f1", "case_id": "case-1"},
        {"fact_id": "cached-f2b", "case_id": "case-2"},
    ]

    loaded_case, review, evidence, facts = CaseService.hydrate_context(
        store, LeakyRepository(), "org-a", "case-1"
    )

    assert loaded_case is case
    assert review.review_id == "review-1"
    assert {item["evidence_id"] for item in evidence} == {"e1"}
    assert {item["fact_id"] for item in facts} == {"f1", "f3", "cached-f1"}
    assert all(item["case_id"] == "case-1" for item in evidence + facts)
