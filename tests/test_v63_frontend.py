import io, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.api_server import ReviewDefenseAPI

def req(app, method, path, body=None, token=None):
    raw=json.dumps(body).encode() if body is not None else b''
    env={'REQUEST_METHOD':method,'PATH_INFO':path,'REMOTE_ADDR':'127.0.0.1','CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw)}
    if token: env['HTTP_AUTHORIZATION']='Bearer '+token
    out={}
    def start(status, headers): out['status']=status; out['headers']=dict(headers)
    data=b''.join(app(env,start))
    return out['status'],out['headers'],data

def test_console_static_routes_and_security_boundary():
    app=ReviewDefenseAPI()
    status,headers,body=req(app,'GET','/app')
    assert status=='200 OK'; assert 'text/html' in headers['Content-Type']; assert b'Review Defense' in body
    status,_,body=req(app,'GET','/assets/app.js')
    assert status=='200 OK'; assert b'/v1/auth/login' in body
    status,_,body=req(app,'GET','/assets/../src/api_server.py')
    assert status == '401 Unauthorized'
    # A normalized traversal path must not expose source files.
    assert b'Production HTTP/API boundary' not in body

def test_frontend_has_no_embedded_secret_or_external_submit_call():
    root=Path(__file__).resolve().parents[1]/'frontend'
    html=(root/'index.html').read_text(); js=(root/'assets/app.js').read_text()
    assert 'access_token' not in html
    assert 'googleapis.com' not in js
    assert 'googleapis.com' not in js
    assert 'fetch("https://www.google.com' not in js
