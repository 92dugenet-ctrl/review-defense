import base64
import io
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.fernet import Fernet

from src.api_server import APIError, ReviewDefenseAPI, User
from src.google_business_profile import GoogleAccount, GoogleLocation, OAuthTokenSet, ReviewSyncResult
from src.review_workspace import ReviewContext


def call(app, method, path, body=None, token=None, query=""):
    raw = json.dumps(body or {}).encode()
    env = {
        "REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
        "CONTENT_LENGTH": str(len(raw)), "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "127.0.0.1", "wsgi.input": io.BytesIO(raw),
    }
    if token:
        env["HTTP_AUTHORIZATION"] = "Bearer " + token
    try:
        status, headers, payload = app.handle(env)
    except APIError as exc:
        status, headers, payload = app._json(
            exc.status,
            {"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )
    if headers.get("Content-Type", "").startswith("application/json"):
        payload = json.loads(payload or b"{}")
    return status, headers, payload


class FakeOAuthClient:
    client_id = "test-client-id"
    def __init__(self, **kwargs):
        self.client_secret = kwargs.get("client_secret")
    def exchange_code(self, *, code, redirect_uri, code_verifier):
        assert code == "auth-code"
        assert code_verifier
        return OAuthTokenSet("access-token", 4_102_444_800, "refresh-token")
    def refresh(self, refresh_token):
        return OAuthTokenSet("refreshed-access-token", 4_102_444_800, refresh_token)


class FakeGoogleClient:
    def __init__(self, *, organization_id, access_token):
        assert organization_id == "org-a"
        assert access_token in {"access-token", "refreshed-access-token"}
    def list_accounts(self, page_token=None):
        return (GoogleAccount("accounts/1", "Acme", "LOCATION_GROUP", "OWNER"),), None
    def list_locations(self, account_id, page_token=None):
        assert account_id == "accounts/1"
        return (GoogleLocation("locations/1", "Acme Paris"),), None
    def list_reviews(self, account_id, location_id, **kwargs):
        assert account_id == "accounts/1" and location_id == "locations/1"
        review = ReviewContext("review-1", "org-a", "locations/1", "Jean", 5, "Très bien",
                              "2026-09-01T10:00:00Z", None, "fr", "GOOGLE", None)
        return ReviewSyncResult((review,), None)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("REVIEW_DEFENSE_GOOGLE_TOKEN_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("REVIEW_DEFENSE_GOOGLE_STATE_KEY", "s" * 48)
    # These endpoint tests exercise the in-memory adapter. PostgreSQL RLS is
    # covered separately by the dedicated DATABASE_URL integration test below.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    api = ReviewDefenseAPI()
    users = {
        "owner": User("user-a", "org-a", "owner@example.com", "hash", "OWNER"),
        "other": User("user-b", "org-b", "other@example.com", "hash", "OWNER"),
        "viewer": User("user-v", "org-a", "viewer@example.com", "hash", "VIEWER"),
    }
    api._auth = lambda environ: users[environ.get("HTTP_AUTHORIZATION", "Bearer owner").split()[-1]]
    return api


def test_profile_is_tenant_scoped_and_validated(app):
    status, _, data = call(app, "POST", "/v1/client/profile",
                           {"legal_name": "Acme SAS", "website": "https://acme.example", "city": "Paris"}, "owner")
    assert status == 200
    assert data["profile"]["legal_name"] == "Acme SAS"
    status, _, data = call(app, "GET", "/v1/client/profile", token="owner")
    assert status == 200 and data["profile"]["city"] == "Paris"
    status, _, data = call(app, "GET", "/v1/client/profile", token="other")
    assert status == 200 and data["profile"] == {}
    status, _, data = call(app, "POST", "/v1/client/profile", {"website": "javascript:alert(1)"}, "owner")
    assert status == 422
    status, _, data = call(app, "POST", "/v1/client/profile", {"legal_name": "Nope"}, "viewer")
    assert status == 403


def test_client_document_upload_list_download_and_tenant_isolation(app):
    pdf = b"%PDF-1.4\nReview Defense test\n"
    body = {"filename": "company.pdf", "content_type": "application/pdf",
            "content_base64": base64.b64encode(pdf).decode(), "category": "COMPANY"}
    status, _, data = call(app, "POST", "/v1/client/documents", body, "owner")
    assert status == 201
    document_id = data["document"]["document_id"]
    assert data["document"]["sha256"]
    status, _, data = call(app, "GET", "/v1/client/documents", token="owner")
    assert status == 200 and data["count"] == 1
    status, _, data = call(app, "GET", "/v1/client/documents", token="other")
    assert status == 200 and data["count"] == 0
    status, headers, payload = call(app, "GET", f"/v1/client/documents/{document_id}/download", token="owner")
    assert status == 200 and payload == pdf and headers["Content-Type"] == "application/pdf"
    status, _, _ = call(app, "GET", f"/v1/client/documents/{document_id}/download", token="other")
    assert status == 404
    bad = {**body, "filename": "../escape.pdf"}
    status, _, _ = call(app, "POST", "/v1/client/documents", bad, "owner")
    assert status == 422
    status, _, _ = call(app, "POST", "/v1/client/documents", body, "viewer")
    assert status == 403


def test_google_oauth_callback_locations_selection_and_replay_protection(app, monkeypatch):
    import src.api_server as api_module
    monkeypatch.setattr(api_module, "GoogleOAuthClient", FakeOAuthClient)
    monkeypatch.setattr(api_module, "GoogleBusinessProfileClient", FakeGoogleClient)
    status, _, data = call(app, "POST", "/v1/integrations/google/start", {}, token="owner")
    assert status == 200
    authorization_url = data["authorization_url"]
    assert "code_challenge_method=S256" in authorization_url
    state = parse_qs(urlsplit(authorization_url).query)["state"][0]
    status, headers, _ = call(app, "GET", "/v1/integrations/google/callback", query="code=auth-code&state=" + state)
    assert status == 302 and "google=connected" in headers["Location"]
    assert len(app.store.google_connections) == 1
    status, _, data = call(app, "GET", "/v1/integrations/google/locations", token="owner")
    assert status == 200 and len(data["items"]) == 1
    item = data["items"][0]
    assert item["location_name"] == "Acme Paris"
    status, _, data = call(app, "POST", "/v1/integrations/google/select-location",
                           {"connection_id": item["connection_id"], "account_id": item["account_id"],
                            "location_id": item["location_id"]}, "owner")
    assert status == 200 and data["reviews_synced"] == 1
    assert ("org-a", "review-1") in app.store.reviews
    status, _, _ = call(app, "GET", "/v1/integrations/google/callback", query="code=auth-code&state=" + state)
    assert status == 400
    assert all("GOOGLE_LOCATION_SELECTED" != e["action"] or e["organization_id"] == "org-a" for e in app.store.audit)


def test_google_selection_rejects_foreign_location(app, monkeypatch):
    import src.api_server as api_module
    monkeypatch.setattr(api_module, "GoogleOAuthClient", FakeOAuthClient)
    monkeypatch.setattr(api_module, "GoogleBusinessProfileClient", FakeGoogleClient)
    status, _, data = call(app, "POST", "/v1/integrations/google/start", {}, token="owner")
    assert status == 200
    state = parse_qs(urlsplit(data["authorization_url"]).query)["state"][0]
    call(app, "GET", "/v1/integrations/google/callback", query="code=auth-code&state=" + state)
    connection_id = next(iter(app.store.google_connections))[1]
    status, _, _ = call(app, "POST", "/v1/integrations/google/select-location",
                        {"connection_id": connection_id, "account_id": "accounts/foreign", "location_id": "locations/1"}, "owner")
    assert status == 403
    assert app.store.google_connections[("org-a", connection_id)]["google_location_id"] is None


def test_google_oauth_start_requires_authorized_role(app):
    status, _, _ = call(app, "POST", "/v1/integrations/google/start", {}, token="viewer")
    assert status == 403

def test_oauth_callback_rls_is_limited_to_the_exact_signed_state():
    root = Path(__file__).resolve().parents[1]
    migration = (root / "migrations/032_v641_google_oauth_state_callback_rls.sql").read_text(encoding="utf-8")
    repository = (root / "src/postgres_api_repository.py").read_text(encoding="utf-8")
    assert "FOR SELECT" in migration and "FOR DELETE" in migration
    assert "state = current_setting('app.google_oauth_state', true)" in migration
    assert "set_config('app.google_oauth_state', %s, true)" in repository


def test_client_hub_is_wired_into_the_served_workspace():
    root = Path(__file__).resolve().parents[1]
    workspace_js = (root / "frontend/workspace.js").read_text(encoding="utf-8")
    workspace_html = (root / "frontend/workspace.html").read_text(encoding="utf-8")
    assert '["client-monitoring","Mon entreprise"]' in workspace_js
    assert 'if(v==="client-monitoring")return await clientMonitoring(el)' in workspace_js
    assert 'post("/v1/integrations/google/start",{})' in workspace_js
    assert '/v1/client/documents/' in workspace_js
    assert 'workspace.js' in workspace_html

def test_postgres_oauth_state_rls_is_forced_and_consumed_atomically():
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        pytest.skip("DATABASE_URL is not configured")
    psycopg = pytest.importorskip("psycopg")
    from psycopg import sql

    conn = psycopg.connect(dsn)
    role_name = "rd_oauth_rls_" + __import__("uuid").uuid4().hex
    try:
        organization_id = conn.execute(
            "INSERT INTO organizations(name) VALUES(%s) RETURNING id",
            ("oauth-rls-test",),
        ).fetchone()[0]
        user_id = conn.execute(
            "INSERT INTO users(email,password_hash) VALUES(%s,%s) RETURNING id",
            (f"oauth-rls-{organization_id}@example.test", "test-hash"),
        ).fetchone()[0]
        state_a = f"oauth-test-a-{organization_id}"
        state_b = f"oauth-test-b-{organization_id}"
        conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role_name)))
        conn.execute(
            sql.SQL("GRANT SELECT, INSERT, DELETE ON google_oauth_states TO {}").format(
                sql.Identifier(role_name)
            )
        )
        conn.execute(
            "SELECT set_config('app.organization_id', %s, true)",
            (str(organization_id),),
        )
        conn.execute(
            "INSERT INTO google_oauth_states(state,organization_id,user_id,code_verifier,expires_at) "
            "VALUES (%s,%s,%s,%s,now()+interval '10 minutes'), "
            "(%s,%s,%s,%s,now()+interval '10 minutes')",
            (state_a, organization_id, user_id, "verifier-a",
             state_b, organization_id, user_id, "verifier-b"),
        )
        conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role_name)))
        bypass = conn.execute(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user"
        ).fetchone()[0]
        assert not bypass
        conn.execute("SELECT set_config('app.organization_id', '', true)")
        conn.execute("SELECT set_config('app.google_oauth_state', %s, true)", (state_a,))
        visible = conn.execute(
            "SELECT state FROM google_oauth_states ORDER BY state"
        ).fetchall()
        assert visible == [(state_a,)]
        consumed = conn.execute(
            "DELETE FROM google_oauth_states WHERE state=%s RETURNING state,organization_id,user_id,code_verifier",
            (state_a,),
        ).fetchone()
        assert consumed == (state_a, organization_id, user_id, "verifier-a")
        assert conn.execute(
            "SELECT count(*) FROM google_oauth_states WHERE state=%s", (state_a,)
        ).fetchone()[0] == 0
        conn.execute("SELECT set_config('app.google_oauth_state', %s, true)", (state_b,))
        assert conn.execute(
            "SELECT state FROM google_oauth_states"
        ).fetchall() == [(state_b,)]
    finally:
        conn.rollback()
        conn.close()
