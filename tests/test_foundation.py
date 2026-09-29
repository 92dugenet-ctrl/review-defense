import io
import json
import pathlib
import subprocess

from src.app import application

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def request(path, method="GET", headers=None):
    status = []
    response_headers = []

    def start(response_status, response_header_list, exc_info=None):
        status.append(response_status)
        response_headers.extend(response_header_list)

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

    body = b"".join(application(env, start))
    return status[0], dict(response_headers), body


def test_health():
    status, headers, body = request("/health")
    assert status == "200 OK"
    assert json.loads(body)["status"] == "ok"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Request-ID"]


def test_request_id_is_propagated():
    status, headers, _ = request("/health", headers={"X-Request-ID": "test-request-123"})
    assert status == "200 OK"
    assert headers["X-Request-ID"] == "test-request-123"


def test_api_metadata():
    status, _, body = request("/api/v1/metadata")
    assert status == "200 OK"
    data = json.loads(body)["data"]
    assert data["service"] == "review-defense"
    assert data["api_version"] == "v1"


def test_api_metadata_method_not_allowed():
    status, _, body = request("/api/v1/metadata", "POST")
    assert status == "405 Method Not Allowed"
    assert json.loads(body)["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_api_health():
    status, _, body = request("/api/v1/health")
    assert status == "200 OK"
    assert json.loads(body)["data"]["status"] == "ok"


def test_api_ready_without_database():
    status, _, body = request("/api/v1/ready")
    assert status in {"200 OK", "503 Service Unavailable"}
    payload = json.loads(body)
    assert payload["data"]["dependencies"]["http"] == "ok"


def test_not_found_is_standard_json():
    status, headers, body = request("/api/v1/unknown")
    assert status == "404 Not Found"
    payload = json.loads(body)
    assert payload["error"]["code"] == "NOT_FOUND"
    assert payload["request_id"]
    assert headers["Content-Type"].startswith("application/json")


def test_method_not_allowed():
    status, _, body = request("/api/v1/health", "POST")
    assert status == "405 Method Not Allowed"
    assert json.loads(body)["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_frontend_shell():
    assert b"Review Defense" in request("/")[2]


def test_frontend_is_only_new_files():
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "frontend").rglob("*") if p.is_file()}
    assert actual == {
        "frontend/index.html",
        "frontend/landing.html",
        "frontend/assets/public.js",
        "frontend/assets/public.css",
        "frontend/assets/seo-articles.js",
    }


def test_js_syntax():
    result = subprocess.run(
        ["node", "--check", str(ROOT / "frontend/assets/public.js")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_migration_runner_tracks_versions():
    text = (ROOT / "scripts/migrate.py").read_text(encoding="utf-8")
    assert "schema_migrations" in text
    assert "applied_at" in text
    assert "INSERT INTO schema_migrations" in text
    assert "pg_advisory_xact_lock" in text


def test_full_legacy_data_model_is_restored():
    files = sorted(MIGRATIONS.glob("*.sql"))
    assert len(files) == 27
    assert files[0].name == "001_initial.sql"
    assert files[-1].name == "027_v642_billing_identifier_integrity.sql"

    required_tables = {
        "organizations",
        "users",
        "memberships",
        "cases",
        "case_events",
        "google_reviews",
        "background_jobs",
        "api_sessions",
        "api_reviews",
        "api_cases",
        "api_decisions",
        "api_evidence",
        "evidence_facts",
        "contradiction_findings",
        "case_escalations",
        "notification_outbox",
        "privacy_requests",
        "privacy_consents",
        "billing_transactions",
    }
    sql = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for table in required_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_data_model_security_contract():
    sql = "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS.glob("*.sql"))
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "current_setting('app.organization_id'" in sql
    assert "lookup_api_session_by_token_hash" in sql
    assert "privacy_requests" in sql
    assert "billing_transactions" in sql


def test_migration_files_are_deterministic():
    from scripts.migrate import migration_files
    assert [path.name for path in migration_files()] == sorted(path.name for path in migration_files())
