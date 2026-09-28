from __future__ import annotations
import json
def api_error(start_response,status,code,message):
    body=json.dumps({"error":{"code":code,"message":message}},ensure_ascii=False).encode()
    start_response(status,[("Content-Type","application/json; charset=utf-8"),("Content-Length",str(len(body))),("Cache-Control","no-store")])
    return [body]
