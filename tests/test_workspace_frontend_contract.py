"""Frontend/API contract checks for the client and admin workspace."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = (ROOT / "frontend" / "workspace.js").read_text(encoding="utf-8")
API = (ROOT / "src" / "api_server.py").read_text(encoding="utf-8")
SEO_RENDERER = (ROOT / "src" / "seo_renderer.py").read_text(encoding="utf-8")


def test_workspace_actions_are_delegated_once_from_app_root():
    assert 'app.addEventListener("click",onAction)' in FRONTEND
    assert 'document.getElementById("modal-root").addEventListener("click",onAction)' not in FRONTEND


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

def test_public_auth_entry_supports_login_and_registration():
    assert 'mode=params.get("auth")==="register"||location.pathname==="/inscription"?"register":"login"' in FRONTEND
    assert 'post("/v1/auth/register",payload)' in FRONTEND
    assert 'post("/v1/auth/login",payload)' in FRONTEND
    assert 'localStorage.setItem("rd_org_id",d.organization_id)' in FRONTEND
    assert 'path == "/v1/auth/register"' in API


def test_public_action_ctas_point_to_auth_entry():
    public_pages = ["index.html", "services.html", "fonctionnement.html", "about.html", "tarif.html", "resources.html"]
    for name in public_pages:
        page = (ROOT / "frontend" / name).read_text(encoding="utf-8")
        assert 'href="/analyse-avis-google/"' not in page
        assert 'href="#try"' not in page
    assert 'href="/inscription"' in (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")

def test_email_verification_link_uses_workspace_auth_screen():
    assert 'location.pathname==="/verify-email"' in FRONTEND
    assert 'post("/v1/auth/email-verification/verify"' in FRONTEND
    assert '"/verify-email"}' in API
    assert 'href="/inscription">Analyser un avis</a>' in SEO_RENDERER
    assert 'href="/inscription">Analyser mon avis →</a>' in SEO_RENDERER

def test_evidence_download_uses_authenticated_tenant_scoped_content_route():
    assert 'path.endswith("/content")' in API
    assert 'self.store.vault.get(organization_id=user.organization_id' in API
    assert 'verify_integrity(content, row["sha256"])' in API
    assert '"/v1/evidence/"+encodeURIComponent(id)+"/content"' in FRONTEND
    assert 'download-evidence:' in FRONTEND

def test_password_recovery_and_invitation_routes_have_frontend_handlers():
    assert 'if(location.pathname==="/reset-password")return resetPassword()' in FRONTEND
    assert 'if(location.pathname==="/accept-invitation")return acceptInvitation()' in FRONTEND
    assert 'post("/v1/auth/recovery/request"' in FRONTEND
    assert 'post("/v1/auth/recovery/reset"' in FRONTEND
    assert 'post("/v1/organization/invitations/accept"' in FRONTEND
    assert 'href="/reset-password">Mot de passe oublié ?' in FRONTEND


def test_auth_route_aliases_serve_the_workspace_shell():
    from wsgi import app

    for route in ["/connexion/", "/inscription/", "/verify-email/", "/reset-password/", "/accept-invitation/"]:
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        body = app(
            {
                "PATH_INFO": route,
                "QUERY_STRING": "",
                "REQUEST_METHOD": "GET",
                "wsgi.url_scheme": "https",
                "SERVER_NAME": "review-defense.test",
                "SERVER_PORT": "443",
                "SCRIPT_NAME": "",
                "REMOTE_ADDR": "127.0.0.1",
                "wsgi.input": __import__("io").BytesIO(),
            },
            start_response,
        )
        assert captured["status"] == "200 OK"
        assert b"/workspace.js" in body[0]
