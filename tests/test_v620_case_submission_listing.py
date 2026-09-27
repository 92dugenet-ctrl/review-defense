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
