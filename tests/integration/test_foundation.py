import io
import json
import pathlib

from wsgi import app

ROOT = pathlib.Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "migrations"
FRONTEND = ROOT / "frontend"


def request(path, method="GET", headers=None):
    status = []
    response_headers = []

    def start(response_status, header_list, exc_info=None):
        status.append(response_status)
        response_headers.extend(header_list)

    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "wsgi.input": io.BytesIO(),
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8080",
        "wsgi.url_scheme": "http",
    }
    for key, value in (headers or {}).items():
        env[f"HTTP_{key.upper().replace('-', '_')}"] = value
    body = b"".join(app(env, start))
    return status[0], dict(response_headers), body


def test_health():
    status, headers, body = request("/health")
    assert status == "200 OK"
    assert json.loads(body)["status"] == "ok"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Request-ID"]


def test_readiness():
    status, _, body = request("/ready")
    assert status in {"200 OK", "503 Service Unavailable"}
    assert json.loads(body)["dependencies"]["http"] == "ok"


def test_api_not_found_requires_authentication():
    status, _, body = request("/v1/unknown")
    assert status == "401 Unauthorized"
    assert json.loads(body)["error"]["code"] in {"AUTH_REQUIRED", "AUTH_INVALID"}


def test_legacy_api_prefix_is_not_exposed():
    status, _, body = request("/api/v1/health")
    assert status == "404 Not Found"
    assert json.loads(body)["error"]["code"] == "NOT_FOUND"


def test_frontend_contract():
    assert (FRONTEND / "index.html").is_file()
    assert (FRONTEND / "styles.css").is_file()
    assert (FRONTEND / "script.js").is_file()
    assert not (FRONTEND / "package.json").exists()
    assert not (FRONTEND / "src").exists()


def test_frontend_shell_serves_static_app():
    status, headers, body = request("/")
    assert status == "200 OK"
    assert headers["Content-Type"].startswith("text/html")
    html = body.decode()
    assert '<link rel="stylesheet" href="styles.css">' in html
    assert '<script src="script.js"></script>' in html


def test_frontend_assets_are_served():
    status, headers, body = request("/styles.css")
    assert status == "200 OK"
    assert headers["Content-Type"].startswith("text/css")
    assert b"--ink:" in body

    status, headers, body = request("/script.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {"text/javascript; charset=utf-8", "application/javascript; charset=utf-8"}
    assert b"setMenu" in body


def test_app_alias_serves_same_frontend():
    root_status, _, root_body = request("/")
    app_status, _, app_body = request("/app")
    assert root_status == app_status == "200 OK"
    assert root_body == app_body


def test_client_and_admin_routes_serve_workspace_assets():
    for path in ("/client", "/client/", "/admin", "/admin/", "/connexion", "/inscription", "/verify-email"):
        status, headers, body = request(path)
        assert status == "200 OK"
        assert headers["Content-Type"].startswith("text/html")
        html = body.decode()
        assert '/workspace.css' in html
        assert '/workspace.js' in html

    status, headers, body = request("/workspace.js")
    assert status == "200 OK"
    assert headers["Content-Type"] in {"text/javascript; charset=utf-8", "application/javascript; charset=utf-8"}
    assert b"async function start()" in body

    status, headers, body = request("/workspace.css")
    assert status == "200 OK"
    assert headers["Content-Type"].startswith("text/css")
    assert b".shell" in body


def test_missing_asset_is_not_spa():
    status, _, body = request("/assets/does-not-exist.js")
    assert status == "404 Not Found"
    assert json.loads(body)["error"]["code"] == "NOT_FOUND"


def test_unknown_public_route_is_not_spa():
    status, _, body = request("/this-route-does-not-exist")
    assert status == "404 Not Found"
    assert json.loads(body)["error"]["code"] == "NOT_FOUND"


def test_migrations_contract():
    files = sorted(MIGRATIONS.glob("*.sql"))
    assert len(files) == 35
    assert files[0].name == "001_initial.sql"
    assert files[-1].name == "034_v646_force_privacy_billing_rls.sql"
    sql = "\n".join(x.read_text() for x in files)
    for table in [
        "organizations",
        "users",
        "memberships",
        "cases",
        "case_events",
        "google_reviews",
        "api_sessions",
        "api_reviews",
        "api_cases",
        "api_evidence",
        "privacy_requests",
        "billing_transactions",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_migration_runner_contract():
    text = (ROOT / "scripts/migrate.py").read_text()
    assert "schema_migrations" in text
    assert "pg_advisory_xact_lock" in text
