import io,json,pathlib,subprocess
from src.app import application
ROOT=pathlib.Path(__file__).resolve().parents[1]
def request(path):
    status=[]; headers=[]
    def start(s,h,exc_info=None): status.append(s); headers.extend(h)
    env={"REQUEST_METHOD":"GET","PATH_INFO":path,"QUERY_STRING":"","wsgi.input":io.BytesIO(),"SERVER_NAME":"localhost","SERVER_PORT":"8080","wsgi.url_scheme":"http"}
    body=b"".join(application(env,start)); return status[0],dict(headers),body
def test_health(): assert json.loads(request("/health")[2])["status"]=="ok"
def test_ready(): assert json.loads(request("/ready")[2])["status"]=="ready"
def test_frontend_shell(): assert b"Review Defense" in request("/")[2]
def test_frontend_is_only_new_files():
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/"frontend").rglob("*") if p.is_file()}
    assert actual=={"frontend/index.html","frontend/landing.html","frontend/assets/public.js","frontend/assets/public.css","frontend/assets/seo-articles.js"}
def test_js_syntax():
    r=subprocess.run(["node","--check",str(ROOT/"frontend/assets/public.js")],capture_output=True,text=True); assert r.returncode==0,r.stderr
