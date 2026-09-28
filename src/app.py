from pathlib import Path
import json
from urllib.parse import unquote
from .config import get_settings
from .database import check_connection
from .errors import api_error
ROOT=Path(__file__).resolve().parents[1]; FRONTEND=ROOT/"frontend"
def response(start_response,status,body,ctype="application/json; charset=utf-8"):
    settings=get_settings()
    headers=[("Content-Type",ctype),("Content-Length",str(len(body))),("Cache-Control","no-store")]
    if settings.secure_headers:
        headers += [("X-Content-Type-Options","nosniff"),("X-Frame-Options","DENY"),("Referrer-Policy","strict-origin-when-cross-origin")]
    start_response(status,headers); return [body]
def j(start_response,status,data): return response(start_response,status,json.dumps(data,ensure_ascii=False).encode())
def static(start_response,path):
    requested=unquote(path.lstrip("/")) or "index.html"; candidate=(FRONTEND/requested).resolve()
    if FRONTEND.resolve() not in candidate.parents or not candidate.is_file(): return api_error(start_response,"404 Not Found","NOT_FOUND","Resource not found")
    ctype={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".svg":"image/svg+xml"}.get(candidate.suffix.lower(),"application/octet-stream")
    return response(start_response,"200 OK",candidate.read_bytes(),ctype)
def application(environ,start_response):
    method=environ.get("REQUEST_METHOD","GET").upper(); path=environ.get("PATH_INFO","/")
    if method=="GET" and path=="/health": return j(start_response,"200 OK",{"status":"ok","service":"review-defense"})
    if method=="GET" and path=="/ready":
        db=check_connection()
        if not db: return j(start_response,"503 Service Unavailable",{"status":"not_ready","dependencies":{"http":"ok","database":"unavailable"}})
        return j(start_response,"200 OK",{"status":"ready","dependencies":{"http":"ok","database":"ok"}})
    if path.startswith("/api/v1/"):
        if path=="/api/v1/health" and method=="GET": return j(start_response,"200 OK",{"data":{"status":"ok"}})
        if path=="/api/v1/health": return api_error(start_response,"405 Method Not Allowed","METHOD_NOT_ALLOWED","Method not allowed")
        return api_error(start_response,"404 Not Found","NOT_FOUND","API route not found")
    if method=="GET" and path in {"/","/app","/app/"}: return static(start_response,"index.html")
    if method=="GET" and path=="/landing.html": return static(start_response,"landing.html")
    if method=="GET" and path.startswith("/assets/"): return static(start_response,path)
    if method=="GET" and path in {"/produit/","/comment-ca-marche/","/services/","/tarifs/","/ressources/","/contact/","/analyse-avis-google/","/ia-et-controle-humain/","/securite/","/confidentialite/"}: return static(start_response,"index.html")
    return api_error(start_response,"404 Not Found","NOT_FOUND","Resource not found")
app=application
