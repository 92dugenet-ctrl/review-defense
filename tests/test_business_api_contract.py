import io
import json
import uuid

from wsgi import app


def request(path, method="GET", payload=None, headers=None):
    status = []
    response_headers = []
    raw = json.dumps(payload or {}).encode()

    def start(response_status, response_header_list, exc_info=None):
        status.append(response_status)
        response_headers.extend(response_header_list)

    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(raw)),
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "127.0.0.1",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8080",
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(raw),
    }
    for key, value in (headers or {}).items():
        env[f"HTTP_{key.upper().replace('-', '_')}"] = value
    body = b"".join(app(env, start))
    return status[0], dict(response_headers), json.loads(body) if body else None


EXPECTED_ROUTE_FAMILIES = {
    "/v1/auth/",
    "/v1/me",
    "/v1/logout",
    "/v1/organization/",
    "/v1/reviews",
    "/v1/evidence",
    "/v1/cases",
    "/v1/review-queue",
    "/v1/escalations",
    "/v1/notifications",
    "/v1/approvals",
    "/v1/submissions",
    "/v1/billing",
    "/v1/paypal/",
    "/v1/privacy/",
}


def test_legacy_business_route_families_are_implemented():
    from src import api_server
    source = api_server.__file__
    text = open(source, encoding="utf-8").read()
    for route in EXPECTED_ROUTE_FAMILIES:
        assert route in text


def test_business_api_requires_authentication():
    for path in (
        "/v1/me",
        "/v1/reviews",
        "/v1/evidence",
        "/v1/cases",
        "/v1/review-queue",
        "/v1/escalations",
        "/v1/notifications",
        "/v1/approvals",
        "/v1/submissions",
        "/v1/billing",
        "/v1/privacy/export",
    ):
        status, _, body = request(path)
        assert status == "401 Unauthorized", (path, body)
        assert body["error"]["code"] in {"AUTH_REQUIRED", "AUTH_INVALID"}


def test_legacy_auth_register_and_authenticated_me():
    email = f"ci-{uuid.uuid4().hex[:12]}@example.test"
    status, _, body = request(
        "/v1/auth/register",
        "POST",
        {"email": email, "organization_name": "CI Review Defense", "password": "StrongPassword123!"},
    )
    assert status == "201 Created", body
    assert body["status"] == "created"
    token = body["access_token"]

    status, _, me = request("/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert status == "200 OK", me
    assert me["email"] == email
    assert me["role"] == "OWNER"


def test_business_api_preserves_health_and_readiness():
    status, _, body = request("/health")
    assert status == "200 OK"
    assert body["service"] == "review-defense"

    status, _, body = request("/ready")
    assert status in {"200 OK", "503 Service Unavailable"}
    assert body["dependencies"]["http"] == "ok"
