from src.api_server import MemoryStore
from src.case_approval_service import CaseApprovalService
from src.decision_workspace import ApprovalEvent


def test_approval_list_reads_persistence_and_memory():
    store = MemoryStore()
    store.approvals.append(
        ApprovalEvent("a-memory", "d2", "c2", "org-a", "owner", "OWNER", "2026-09-28T01:00:00Z", "sha-memory")
    )
    class Repo:
        def list_approvals(self, organization_id):
            return [{"approval_id":"a-db","decision_id":"d1","case_id":"c1","organization_id":organization_id,
                     "actor_id":"admin","actor_role":"ADMIN","snapshot_sha256":"sha-db","approved_at":"2026-09-28T00:00:00Z"}]
    rows = CaseApprovalService(store=store, repository=Repo()).list_for_organization(organization_id="org-a")
    assert {x["approval_id"] for x in rows} == {"a-db","a-memory"}


def test_memory_approval_wins_on_duplicate_id():
    store = MemoryStore()
    store.approvals.append(
        ApprovalEvent("a1", "d1", "c1", "org-a", "admin", "ADMIN", "2026-09-28T01:00:00Z", "sha-new")
    )
    class Repo:
        def list_approvals(self, organization_id):
            return [{"approval_id":"a1","decision_id":"d1","case_id":"c1","organization_id":organization_id,
                     "actor_id":"admin","actor_role":"ADMIN","snapshot_sha256":"sha-old","approved_at":"2026-09-28T00:00:00Z"}]
    row = CaseApprovalService(store=store, repository=Repo()).list_for_organization(organization_id="org-a")[0]
    assert row["snapshot_sha256"] == "sha-new"
