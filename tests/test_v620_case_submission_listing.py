from src.api_server import MemoryStore
from src.case_submission_service import CaseSubmissionService


def test_list_is_tenant_scoped():
    store = MemoryStore()
    store.submissions[("org-a", "s1")] = {"submission_id": "s1", "organization_id": "org-a"}
    store.submissions[("org-b", "s2")] = {"submission_id": "s2", "organization_id": "org-b"}

    service = CaseSubmissionService(store=store)

    assert service.list_for_organization(organization_id="org-a") == [
        {"submission_id": "s1", "organization_id": "org-a"}
    ]

class RecordingRepository:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def list_submissions(self, organization_id):
        self.calls.append(("list_submissions", organization_id))
        return [row for row in self.rows if row["organization_id"] == organization_id]


def test_list_merges_persistent_rows_and_memory_overrides():
    store = MemoryStore()
    store.submissions[("org-a", "s1")] = {
        "submission_id": "s1",
        "organization_id": "org-a",
        "case_id": "c1",
        "status": "DRAFT",
        "external_call": False,
    }
    repo = RecordingRepository([
        {"submission_id": "s1", "organization_id": "org-a", "case_id": "c1", "status": "SUBMITTED", "external_call": False},
        {"submission_id": "s2", "organization_id": "org-a", "case_id": "c2", "status": "DRAFT", "external_call": False},
        {"submission_id": "s3", "organization_id": "org-b", "case_id": "c3", "status": "DRAFT", "external_call": False},
    ])
    service = CaseSubmissionService(store=store, repository=repo)

    rows = service.list_for_organization(organization_id="org-a")

    assert rows == [
        store.submissions[("org-a", "s1")],
        {"submission_id": "s2", "organization_id": "org-a", "case_id": "c2", "status": "DRAFT", "external_call": False},
    ]
    assert repo.calls == [("list_submissions", "org-a")]
