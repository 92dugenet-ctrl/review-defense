from pathlib import Path
import json
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]; FRONTEND=ROOT/"frontend"
def response(start_response,status,body,ctype="application/json; charset=utf-8"):
    start_response(status,[("Content-Type",ctype),("Content-Length",str(len(body))),("Cache-Control","no-store")]); return [body]
def j(start_response,status,data): return response(start_response,status,json.dumps(data).encode())
def static(start_response,path):
    requested=unquote(path.lstrip("/")) or "index.html"; candidate=(FRONTEND/requested).resolve()
    if FRONTEND.resolve() not in candidate.parents or not candidate.is_file(): return j(start_response,"404 Not Found",{"error":"not_found"})
    ctype={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".svg":"image/svg+xml"}.get(candidate.suffix.lower(),"application/octet-stream")
    return response(start_response,"200 OK",candidate.read_bytes(),ctype)
def application(environ,start_response):
    method=environ.get("REQUEST_METHOD","GET").upper(); path=environ.get("PATH_INFO","/")
    if method=="GET" and path=="/health": return j(start_response,"200 OK",{"status":"ok","service":"review-defense"})
    if method=="GET" and path=="/ready": return j(start_response,"200 OK",{"status":"ready","dependencies":{"http":"ok"}})
    if method=="GET" and path in {"/","/app","/app/"}: return static(start_response,"index.html")
    if method=="GET" and path=="/landing.html": return static(start_response,"landing.html")
    if method=="GET" and path.startswith("/assets/"): return static(start_response,path)
    if method=="GET" and path in {"/produit/","/comment-ca-marche/","/services/","/tarifs/","/ressources/","/contact/","/analyse-avis-google/","/ia-et-controle-humain/","/securite/","/confidentialite/"}: return static(start_response,"index.html")
    return j(start_response,"404 Not Found",{"error":"not_found"})
app=application
