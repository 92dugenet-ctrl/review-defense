from src.api_server import MemoryStore
from src.case_evidence_matrix_service import CaseEvidenceMatrixService
from src.case_service import Case
from src.review_workspace import ReviewContext


def test_build_is_case_and_tenant_scoped():
    store = MemoryStore()
    case = Case("c1", "org-a", "r1", "ANALYZING", "2026-09-20T12:00:00Z")
    store.reviews[("org-a", "r1")] = ReviewContext(
        "r1", "org-a", "loc", "Author", 1, "Bad service", "2026-09-20T11:00:00Z"
    )
    store.evidence[("org-a", "e1")] = {
        "evidence_id": "e1", "case_id": "c1", "sha256": "abc", "verified": True
    }
    service = CaseEvidenceMatrixService(store=store)

    matrix = service.build(organization_id="org-a", case=case)

    assert matrix
    assert all(row["requires_human_review"] is True for row in matrix)


def test_build_requires_review():
    store = MemoryStore()
    case = Case("c1", "org-a", "missing", "ANALYZING", "2026-09-20T12:00:00Z")
    service = CaseEvidenceMatrixService(store=store)

    try:
        service.build(organization_id="org-a", case=case)
    except KeyError as exc:
        assert str(exc) == "'review not found'"
    else:
        raise AssertionError("missing review should fail")
