import io
import json
import os
import uuid

import psycopg

from src.api_server import create_app
from src.postgres_api_repository import PostgresAPIRepository
from src.production_config import ProductionConfig


def request(app, path, method="GET", payload=None, token=None):
    body = json.dumps(payload or {}).encode()
    status = []
    headers = []

    def start(response_status, response_headers, exc_info=None):
        status.append(response_status)
        headers.extend(response_headers)

    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "127.0.0.1",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8080",
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(body),
    }
    if token:
        env["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    raw = b"".join(app(env, start))
    return status[0], dict(headers), json.loads(raw) if raw else None


def make_app(dsn):
    repo = PostgresAPIRepository(dsn)
    config = ProductionConfig.from_env()
    return create_app(repository=repo, config=config)


def test_postgres_schema_and_rls_contract():
    dsn = os.environ["DATABASE_URL"]
    with psycopg.connect(dsn) as conn:
        assert conn.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 33
        assert conn.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1").fetchone()[0] == "033_v641_client_hub_force_rls"
        rls = conn.execute("""
            SELECT count(*) FROM pg_class c
            JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='public' AND c.relname IN
              ('memberships','cases','case_events','api_reviews','api_cases','api_sessions','billing_accounts')
              AND c.relrowsecurity
        """).fetchone()[0]
        assert rls == 7


def test_end_to_end_persistent_client_analysis_result_history_and_permissions():
    dsn = os.environ["DATABASE_URL"]
    app = make_app(dsn)
    email = f"integration-{uuid.uuid4().hex[:10]}@example.test"
    password = "StrongPassword123!"

    status, _, created = request(
        app, "/v1/auth/register", "POST",
        {"email": email, "organization_name": "Integration Tenant", "password": password},
    )
    assert status == "201 Created", created
    token = created["access_token"]
    organization_id = created["organization_id"]

    status, _, me = request(app, "/v1/me", token=token)
    assert status == "200 OK"
    assert me["organization_id"] == organization_id
    assert me["role"] == "OWNER"

    review_id = f"review-{uuid.uuid4().hex}"
    status, _, review = request(
        app, "/v1/reviews", "POST",
        {
            "review_id": review_id,
            "location_id": "location-1",
            "author_display_name": "Integration Client",
            "rating": 1,
            "text": "Service received but issue remains unresolved.",
            "published_at": "2026-09-29T08:00:00+00:00",
        },
        token,
    )
    assert status == "201 Created"
    assert review["review"]["review_id"] == review_id

    # Rebuild the API process to prove the authenticated session and review survive
    # outside the original in-memory store.
    app = make_app(dsn)
    status, _, analysis = request(app, f"/v1/reviews/{review_id}", token=token)
    assert status == "200 OK"
    assert analysis["review"]["review_id"] == review_id
    assert analysis["claims"]
    assert "policy_signals" in analysis

    status, _, case_response = request(
        app, "/v1/cases", "POST", {"review_id": review_id}, token
    )
    assert status == "201 Created", case_response
    case_id = case_response["case"]["case_id"]

    status, _, case_result = request(app, f"/v1/cases/{case_id}", token=token)
    assert status == "200 OK"
    assert case_result["case"]["case_id"] == case_id
    assert case_result["review"]["review_id"] == review_id
    assert case_result["claims"]

    status, _, history = request(app, f"/v1/cases/{case_id}/history", token=token)
    assert status == "200 OK"
    assert history["count"] >= 1
    assert any(item["event_type"] == "CASE_CREATED" for item in history["items"])

    # Owner-only decision endpoint must reject a CLIENT.
    repo = PostgresAPIRepository(dsn)
    client_email = f"client-{uuid.uuid4().hex[:10]}@example.test"
    client_id, _, _, _ = repo.create_user(
        organization_id, client_email, __import__("src.security_hardening", fromlist=["hash_password"]).hash_password(password), "CLIENT"
    )
    login_status, _, login = request(
        app, "/v1/auth/login", "POST",
        {"email": client_email, "organization_id": organization_id, "password": password},
    )
    assert login_status == "200 OK"
    client_token = login["access_token"]

    status, _, forbidden = request(
        app, f"/v1/cases/{case_id}/decision", "POST",
        {"kind": "HUMAN_REVIEW", "rationale": "not permitted for client role"},
        client_token,
    )
    assert status == "403 Forbidden"
    assert forbidden["error"]["code"] == "FORBIDDEN"

    # A second tenant cannot see the first tenant's review or case.
    other = request(
        app, "/v1/auth/register", "POST",
        {"email": f"other-{uuid.uuid4().hex[:10]}@example.test", "organization_name": "Other Tenant", "password": password},
    )[2]
    other_token = other["access_token"]
    status, _, other_reviews = request(app, "/v1/reviews", token=other_token)
    assert status == "200 OK"
    assert all(item["review_id"] != review_id for item in other_reviews["items"])
    status, _, missing_review = request(app, f"/v1/reviews/{review_id}", token=other_token)
    assert status == "404 Not Found"
    assert missing_review["error"]["code"] == "NOT_FOUND"
    status, _, missing_case = request(app, f"/v1/cases/{case_id}", token=other_token)
    assert status == "404 Not Found"
    assert missing_case["error"]["code"] == "NOT_FOUND"


def test_admin_workspace_permissions_and_session_revocation():
    dsn = os.environ["DATABASE_URL"]
    app = make_app(dsn)
    password = "StrongPassword123!"
    owner_email = f"admin-owner-{uuid.uuid4().hex[:10]}@example.test"

    status, _, owner = request(
        app, "/v1/auth/register", "POST",
        {"email": owner_email, "organization_name": "Admin Integration Tenant", "password": password},
    )
    assert status == "201 Created", owner
    owner_token = owner["access_token"]
    organization_id = owner["organization_id"]

    repo = PostgresAPIRepository(dsn)
    from src.security_hardening import hash_password
    owner_record = repo.get_user_by_email(organization_id, owner_email)
    assert owner_record is not None
    owner_id = str(owner_record[0])
    admin_email = f"admin-{uuid.uuid4().hex[:10]}@example.test"
    admin_id, _, _, _ = repo.create_user(
        organization_id, admin_email, hash_password(password), "ADMIN"
    )

    status, _, admin_login = request(
        app, "/v1/auth/login", "POST",
        {"email": admin_email, "organization_id": organization_id, "password": password},
    )
    assert status == "200 OK", admin_login
    admin_token = admin_login["access_token"]

    status, _, members = request(app, "/v1/organization/members", token=admin_token)
    assert status == "200 OK"
    assert any(m["user_id"] == str(admin_id) and m["role"] == "ADMIN" for m in members["items"])

    invite_email = f"invite-{uuid.uuid4().hex[:10]}@example.test"
    status, _, invitation = request(
        app, "/v1/organization/invitations", "POST",
        {"email": invite_email, "role": "CLIENT"}, admin_token,
    )
    assert status == "201 Created", invitation
    assert invitation["email"] == invite_email
    assert invitation["role"] == "CLIENT"
    assert invitation["invitation_token"]

    status, _, changed = request(
        app, f"/v1/organization/members/{admin_id}/role", "POST",
        {"role": "ANALYST"}, owner_token,
    )
    assert status == "200 OK"
    assert changed["role"] == "ANALYST"

    persisted = repo.get_user_by_email(organization_id, admin_email)
    assert persisted is not None
    assert persisted[3] == "ANALYST"

    # A role change invalidates the previous elevated session.
    status, _, stale = request(app, "/v1/me", token=admin_token)
    assert status == "401 Unauthorized"
    assert stale["error"]["code"] == "AUTH_INVALID"

    status, _, refreshed_login = request(
        app, "/v1/auth/login", "POST",
        {"email": admin_email, "organization_id": organization_id, "password": password},
    )
    assert status == "200 OK"
    refreshed_token = refreshed_login["access_token"]
    assert refreshed_login["role"] == "ANALYST"

    status, _, refreshed = request(app, "/v1/me", token=refreshed_token)
    assert status == "200 OK"
    assert refreshed["role"] == "ANALYST"

    status, _, forbidden = request(
        app, f"/v1/organization/members/{owner_id}/role", "POST",
        {"role": "ADMIN"}, refreshed_token,
    )
    assert status == "403 Forbidden"
    assert forbidden["error"]["code"] == "FORBIDDEN"

    status, _, forbidden_owner = request(
        app, "/v1/organization/invitations", "POST",
        {"email": f"owner-invite-{uuid.uuid4().hex[:8]}@example.test", "role": "OWNER"}, refreshed_token,
    )
    assert status == "403 Forbidden"
    assert forbidden_owner["error"]["code"] == "FORBIDDEN"

    status, _, revoked = request(
        app, "/v1/auth/revoke-all", "POST", {"user_id": str(admin_id)}, owner_token,
    )
    assert status == "200 OK"
    assert revoked["status"] == "sessions_revoked"

    status, _, invalid = request(app, "/v1/me", token=refreshed_token)
    assert status == "401 Unauthorized"
    assert invalid["error"]["code"] == "AUTH_INVALID"
