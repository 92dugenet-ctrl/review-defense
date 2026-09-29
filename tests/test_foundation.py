import io
import json
import pathlib

from src.app import application

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"
FRONTEND = ROOT / "frontend"


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


def test_frontend_build_contract():
    package = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    assert package["type"] == "module"
    assert package["scripts"]["build"] == "tsc -b && vite build"
    assert (FRONTEND / "src/main.tsx").is_file()
    assert (FRONTEND / "src/app/router.tsx").is_file()
    assert (FRONTEND / "vite.config.ts").is_file()
    assert (FRONTEND / "dist/index.html").is_file()
    assert (FRONTEND / "src/auth/AuthContext.tsx").is_file()
    assert (FRONTEND / "src/auth/RequireAuth.tsx").is_file()
    assert (FRONTEND / "src/pages/LoginPage.tsx").is_file()
    assert (FRONTEND / "src/pages/RegisterPage.tsx").is_file()


def test_frontend_layout_contract():
    shell = (FRONTEND / "src/components/layout/AppShell.tsx").read_text(encoding="utf-8")
    css = (FRONTEND / "src/styles/global.css").read_text(encoding="utf-8")
    assert "NavLink" in shell
    assert "Outlet" in shell
    assert "mobileOpen" in shell
    assert 'aria-label="Navigation principale"' in shell
    assert 'role === "admin"' in shell
    assert ".sidebar.mobile-open" in css
    assert ".sidebar-backdrop" in css
    assert ".topbar" in css
    assert "@media (max-width: 900px)" in css


def test_frontend_shell_serves_built_react_app():
    status, headers, body = request("/")
    assert status == "200 OK"
    assert headers["Content-Type"].startswith("text/html")
    assert b'<div id="root"></div>' in body
    assert b"Review Defense" in body
    assert b"/assets/" in body


def test_frontend_spa_routes_serve_built_shell():
    for path in ("/app", "/app/dashboard", "/reviews", "/login", "/register"):
        status, headers, body = request(path)
        assert status == "200 OK", path
        assert headers["Content-Type"].startswith("text/html"), path
        assert b'<div id="root"></div>' in body, path


def test_frontend_missing_asset_is_not_hidden_by_spa_fallback():
    status, _, body = request("/assets/does-not-exist.js")
    assert status == "404 Not Found"
    assert json.loads(body)["error"]["code"] == "NOT_FOUND"


def test_legacy_frontend_files_are_not_required():
    for path in (
        FRONTEND / "landing.html",
        FRONTEND / "assets" / "public.js",
        FRONTEND / "assets" / "public.css",
        FRONTEND / "assets" / "billing.js",
        FRONTEND / "assets" / "seo-articles.js",
    ):
        assert not path.exists(), path


def test_migration_runner_tracks_versions():
    text = (ROOT / "scripts/migrate.py").read_text(encoding="utf-8")
    assert "schema_migrations" in text
    assert "applied_at" in text
    assert "INSERT INTO schema_migrations" in text
    assert "pg_advisory_xact_lock" in text


def test_full_legacy_data_model_is_restored():
    files = sorted(MIGRATIONS.glob("*.sql"))
    assert len(files) == 30
    assert files[0].name == "001_initial.sql"
    assert files[-1].name == "030_v644_billing_account_state.sql"

    required_tables = {
        "organizations", "users", "memberships", "cases", "case_events",
        "google_reviews", "background_jobs", "api_sessions", "api_reviews",
        "api_cases", "api_decisions", "api_evidence", "evidence_facts",
        "contradiction_findings", "case_escalations", "notification_outbox",
        "privacy_requests", "privacy_consents", "billing_transactions",
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

def test_dashboard_frontend_contract():
    page = (FRONTEND / "src/pages/DashboardPage.tsx").read_text(encoding="utf-8")
    types = (FRONTEND / "src/types/api.ts").read_text(encoding="utf-8")
    assert '"/v1/reviews"' in page
    assert '"/v1/cases"' in page
    assert '"/v1/review-queue"' in page
    assert '"/v1/notifications"' in page
    assert "Promise.all" in page
    assert "ReviewQueueItem" in types
    assert "NotificationItem" in types
    assert "dashboard-kpis" in page
    assert "dashboard-card" in page

def test_reviews_frontend_contract():
    page = (FRONTEND / "src/pages/ReviewsPage.tsx").read_text(encoding="utf-8")
    detail = (FRONTEND / "src/pages/ReviewDetailPage.tsx").read_text(encoding="utf-8")
    router = (FRONTEND / "src/app/router.tsx").read_text(encoding="utf-8")
    assert '"/v1/reviews"' in page
    assert '"/v1/reviews/"' in detail
    assert "reviews/:reviewId" in router
    assert "reviews-toolbar" in page
    assert "policy_signals" in detail
    assert "claims" in detail

def test_frontend_modules_6_to_10_contract():
    router = (FRONTEND / "src/app/router.tsx").read_text(encoding="utf-8")
    expected = ["CasesPage", "CaseDetailPage", "AnalysisPage", "NotificationsPage", "BillingPage", "PrivacyPage"]
    for name in expected:
        assert name in router
    cases = (FRONTEND / "src/pages/CasesPage.tsx").read_text(encoding="utf-8")
    detail = (FRONTEND / "src/pages/CaseDetailPage.tsx").read_text(encoding="utf-8")
    analysis = (FRONTEND / "src/pages/AnalysisPage.tsx").read_text(encoding="utf-8")
    notifications = (FRONTEND / "src/pages/NotificationsPage.tsx").read_text(encoding="utf-8")
    billing = (FRONTEND / "src/pages/BillingPage.tsx").read_text(encoding="utf-8")
    privacy = (FRONTEND / "src/pages/PrivacyPage.tsx").read_text(encoding="utf-8")
    assert '"/v1/cases"' in cases and '"/v1/cases/"' in detail
    assert '"/v1/review-queue"' in analysis and '"/v1/review-queue/workload"' in analysis
    assert '"/v1/notifications"' in notifications
    assert '"/v1/billing"' in billing and '"/v1/billing/catalog"' in billing
    assert '"/v1/privacy/export"' in privacy and '"/v1/privacy/requests"' in privacy


def test_dashboard_visual_contract():
    page=(FRONTEND/"src/pages/DashboardPage.tsx").read_text(encoding="utf-8")
    css=(FRONTEND/"src/styles/global.css").read_text(encoding="utf-8")
    assert "dashboard-hero" in page and "dashboard-metrics" in page
    assert "dashboard-main-grid" in page and "dashboard-surface" in page
    assert "dashboard-metric-focus" in css and "dashboard-next-content" in css
