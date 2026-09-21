from src.app_shell import SessionContext, can_access

def test_tenant_context_is_required():
    s = SessionContext("u1", "org-a", "ANALYST")
    assert s.organization_id == "org-a"

def test_roles():
    assert can_access(SessionContext("u1","org-a","ANALYST"), "/cases")
    assert not can_access(SessionContext("u2","org-b","CLIENT"), "/approvals")

def test_viewer_is_read_only_surface():
    s = SessionContext("u3","org-a","VIEWER")
    assert can_access(s, "/analytics")
    assert not can_access(s, "/evidence")

def test_unknown_role_denied():
    assert not can_access(SessionContext("u4","org-a","SUPERUSER"), "/")
