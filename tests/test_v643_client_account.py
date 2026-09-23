from pathlib import Path
import io, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def test_client_activation_ui_is_available():
    public = (ROOT / "frontend/assets/public.js").read_text(encoding="utf-8")
    app = (ROOT / "frontend/assets/app.js").read_text(encoding="utf-8")
    assert "invitationSignupPage" in public
    assert "/v1/organization/invitations/accept" in public
    assert "Créer mon compte" in public
    assert "location.pathname==='/accept-invitation'" in app

def test_client_console_hides_admin_operational_sections():
    app = (ROOT / "frontend/assets/app.js").read_text(encoding="utf-8")
    assert "CLIENT:new Set" in app
    assert "'dashboard','reviews','cases','evidence','alerts','analytics'" in app

def test_client_invitation_acceptance_can_load_from_persistent_repository():
    from src.api_server import ReviewDefenseAPI, User
    class Repo:
        def get_invitation_by_token(self, organization_id, token_hash):
            return ("inv-1", organization_id, "client@example.com", "CLIENT", token_hash,
                    datetime.now(timezone.utc).replace(microsecond=0), "owner-1", None, None)
        def create_user(self, organization_id, email, password_hash, role):
            return ("client-1", email, password_hash, role)
        def set_email_unverified(self, organization_id, user_id): pass
        def mark_invitation_accepted(self, organization_id, invitation_id): return True
    app=ReviewDefenseAPI()
    app.repository=Repo()
    from dataclasses import replace
    app.config = replace(app.config, require_email_verification=False)
    body=json.dumps({"organization_id":"org-1","email":"client@example.com","invitation_token":"tok","password":"StrongPassword123!"}).encode()
    env={"REQUEST_METHOD":"POST","PATH_INFO":"/v1/organization/invitations/accept","REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(body)),"wsgi.input":io.BytesIO(body)}
    out={}
    def start(status,headers): out["status"]=status
    payload=b"".join(app(env,start))
    data=json.loads(payload)
    assert out["status"]=="200 OK"
    assert data["role"]=="CLIENT"
    assert data["access_token"]

def test_client_workspace_does_not_render_sensitive_action_controls():
    app = (ROOT / "frontend/assets/app.js").read_text(encoding="utf-8")
    assert "const canAct=['OWNER','ADMIN','ANALYST'].includes(state.me?.role)" in app
    assert "Lecture client · les décisions sensibles sont réservées aux rôles habilités." in app

def test_self_service_signup_endpoint_creates_owner_account():
    from src.api_server import ReviewDefenseAPI
    import io, json
    api = ReviewDefenseAPI()
    body = json.dumps({"organization_name":"Acme Test","email":"owner@example.com","password":"StrongPassword123!"}).encode()
    env={"REQUEST_METHOD":"POST","PATH_INFO":"/v1/auth/register","REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(body)),"wsgi.input":io.BytesIO(body)}
    out={}
    def start(status,headers): out["status"]=status
    payload=b"".join(api(env,start))
    data=json.loads(payload)
    assert out["status"]=="201 Created"
    assert data["status"]=="created"
    assert data["role"]=="OWNER"
    assert data["access_token"]

def test_public_site_offers_direct_signup_and_invitation_paths():
    public=(ROOT/"frontend/assets/public.js").read_text(encoding="utf-8")
    app=(ROOT/"frontend/assets/app.js").read_text(encoding="utf-8")
    assert "renderSignup" in public
    assert "/v1/auth/register" in app
    assert "Créer un compte" in app
    assert "J’ai une invitation" in app
