"""Frontend/API contract checks for the client and admin workspace."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = (ROOT / "frontend" / "workspace.js").read_text(encoding="utf-8")
API = (ROOT / "src" / "api_server.py").read_text(encoding="utf-8")


def test_workspace_actions_are_delegated_from_both_surfaces():
    assert 'app.addEventListener("click",onAction)' in FRONTEND
    assert 'document.getElementById("modal-root").addEventListener("click",onAction)' in FRONTEND


def test_invitation_and_role_controls_use_existing_api_routes():
    assert 'post("/v1/organization/invitations"' in FRONTEND
    assert '"/v1/organization/members/"+encodeURIComponent(id)+"/role"' in FRONTEND
    assert 'path == "/v1/organization/invitations"' in API
    assert 'path.endswith("/role")' in API


def test_escalation_actions_match_existing_api_routes():
    assert '"/v1/escalations/"+encodeURIComponent' in FRONTEND
    assert 'path.endswith("/acknowledge")' in API
    assert 'path.endswith("/resolve")' in API
    assert 'path.endswith("/notify")' in API
    assert 'notify-escalation:' in FRONTEND


def test_notification_actions_match_existing_api_routes():
    assert '"/v1/notifications/"+encodeURIComponent(id)+"/"' in FRONTEND
    assert 'path.endswith("/deliver")' in API
    assert 'path.endswith("/cancel")' in API

def test_notification_target_guidance_matches_channel():
    assert 'channel==="EMAIL"' in FRONTEND
    assert 'channel==="WEBHOOK"' in FRONTEND
    assert 'S.userEmail=me.email||null' in FRONTEND


def test_assignment_controls_respect_the_current_assignee():
    assert 'assignedTo!==S.userId&&!can("manager")' in FRONTEND
    assert 'only the assignee or manager may unclaim' in API


def test_workspace_javascript_parses_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        import pytest
        pytest.skip("Node.js is not installed in this test environment")
    subprocess.run([node, "--check", str(ROOT / "frontend" / "workspace.js")],
                   check=True, capture_output=True, text=True)
