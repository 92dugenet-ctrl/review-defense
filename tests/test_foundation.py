import io,json,pathlib,subprocess
from src.app import application
ROOT=pathlib.Path(__file__).resolve().parents[1]
def request(path,method="GET"):
    status=[]; headers=[]
    def start(s,h,exc_info=None): status.append(s); headers.extend(h)
    env={"REQUEST_METHOD":method,"PATH_INFO":path,"QUERY_STRING":"","wsgi.input":io.BytesIO(),"SERVER_NAME":"localhost","SERVER_PORT":"8080","wsgi.url_scheme":"http"}
    body=b"".join(application(env,start)); return status[0],dict(headers),body
def test_health():
    status,headers,body=request("/health"); assert status=="200 OK"; assert json.loads(body)["status"]=="ok"; assert headers["X-Content-Type-Options"]=="nosniff"
def test_api_metadata():
    status,_,body=request("/api/v1/metadata"); assert status=="200 OK"; assert json.loads(body)["data"]=={"service":"review-defense","api_version":"v1"}

def test_api_metadata_method_not_allowed():
    status,_,body=request("/api/v1/metadata","POST"); assert status=="405 Method Not Allowed"; assert json.loads(body)["error"]["code"]=="METHOD_NOT_ALLOWED"

def test_api_health():
    status,_,body=request("/api/v1/health"); assert status=="200 OK"; assert json.loads(body)["data"]["status"]=="ok"
def test_not_found_is_standard_json():
    status,headers,body=request("/api/v1/unknown"); assert status=="404 Not Found"; assert json.loads(body)["error"]["code"]=="NOT_FOUND"; assert headers["Content-Type"].startswith("application/json")
def test_method_not_allowed():
    status,_,body=request("/api/v1/health","POST"); assert status=="405 Method Not Allowed"; assert json.loads(body)["error"]["code"]=="METHOD_NOT_ALLOWED"
def test_frontend_shell(): assert b"Review Defense" in request("/")[2]
def test_frontend_is_only_new_files():
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/"frontend").rglob("*") if p.is_file()}
    assert actual=={"frontend/index.html","frontend/landing.html","frontend/assets/public.js","frontend/assets/public.css","frontend/assets/seo-articles.js"}
def test_js_syntax():
    r=subprocess.run(["node","--check",str(ROOT/"frontend/assets/public.js")],capture_output=True,text=True); assert r.returncode==0,r.stderr
def test_migration_runner_tracks_versions():
    text=(ROOT/"scripts/migrate.py").read_text(encoding="utf-8")
    assert "schema_migrations" in text
    assert "applied_at" in text
    assert "INSERT INTO schema_migrations" in text
