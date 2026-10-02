import io,json,pathlib
from src.app import application
ROOT=pathlib.Path(__file__).resolve().parents[1]; MIGRATIONS=ROOT/"migrations"; FRONTEND=ROOT/"frontend"
def request(path,method="GET",headers=None):
 status=[];rh=[]
 def start(s,h,exc_info=None):status.append(s);rh.extend(h)
 env={"REQUEST_METHOD":method,"PATH_INFO":path,"QUERY_STRING":"","wsgi.input":io.BytesIO(),"SERVER_NAME":"localhost","SERVER_PORT":"8080","wsgi.url_scheme":"http"}
 for k,v in (headers or {}).items():env["HTTP_"+k.upper().replace("-","_")]=v
 body=b"".join(application(env,start));return status[0],dict(rh),body
def test_health():
 s,h,b=request("/health");assert s=="200 OK";assert json.loads(b)["status"]=="ok";assert h["X-Content-Type-Options"]=="nosniff";assert h["X-Request-ID"]
def test_api_metadata():
 s,_,b=request("/api/v1/metadata");assert s=="200 OK";d=json.loads(b)["data"];assert d["service"]=="review-defense";assert d["api_version"]=="v1"
def test_api_health():
 s,_,b=request("/api/v1/health");assert s=="200 OK";assert json.loads(b)["data"]["status"]=="ok"
def test_api_not_found():
 s,_,b=request("/api/v1/unknown");assert s=="404 Not Found";assert json.loads(b)["error"]["code"]=="NOT_FOUND"
def test_frontend_contract():
 p=json.loads((FRONTEND/"package.json").read_text());assert p["scripts"]["build"]=="tsc -b && vite build"
 for path in ["src/main.tsx","src/app/router.tsx","src/components/layout/AppShell.tsx","src/pages/HomePage.tsx","src/pages/DashboardPage.tsx","src/pages/AdminPage.tsx","src/styles/global.css"]:assert (FRONTEND/path).is_file()
def test_marketing_contract():
 page=(FRONTEND/"src/pages/HomePage.tsx").read_text();assert "story-section" in page and "security-section" in page and "pricing" in page and "Créer mon espace" in page
def test_client_routes_contract():
 router=(FRONTEND/"src/app/router.tsx").read_text()
 for route in ["dashboard","reviews","cases","analysis","notifications","billing","settings","privacy"]:assert 'path:"'+route+'"' in router
def test_admin_contract():
 p=(FRONTEND/"src/pages/AdminPage.tsx").read_text();assert '"/v1/organization/members"' in p and '"/v1/organization/invitations"' in p and '"/v1/auth/revoke-all"' in p
def test_billing_paypal_contract():
 p=(FRONTEND/"src/pages/BillingPage.tsx").read_text();assert "paypal.com/sdk/js" in p and "/v1/paypal/subscription/confirm" in p and "createSubscription" in p
def test_settings_privacy_split():
 r=(FRONTEND/"src/app/router.tsx").read_text();assert 'path:"settings"' in r and 'path:"privacy"' in r
def test_frontend_shell_serves_built_app():
 s,h,b=request("/");assert s=="200 OK";assert h["Content-Type"].startswith("text/html");assert b'<div id="root"></div>' in b
def test_missing_asset_is_not_spa():
 s,_,b=request("/assets/does-not-exist.js");assert s=="404 Not Found";assert json.loads(b)["error"]["code"]=="NOT_FOUND"
def test_migrations_contract():
 files=sorted(MIGRATIONS.glob("*.sql"));assert len(files)==30;assert files[0].name=="001_initial.sql";assert files[-1].name=="030_v644_billing_account_state.sql"
 sql="\n".join(x.read_text() for x in files)
 for table in ["organizations","users","memberships","cases","case_events","google_reviews","api_sessions","api_reviews","api_cases","api_evidence","privacy_requests","billing_transactions"]:assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
def test_migration_runner_contract():
 t=(ROOT/"scripts/migrate.py").read_text();assert "schema_migrations" in t and "pg_advisory_xact_lock" in t
