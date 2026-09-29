from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

from .config import get_settings
from .database import check_connection
from .errors import api_error

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
API_VERSION = "v1"
SERVICE_NAME = "review-defense"


def _headers(body: bytes, content_type: str = "application/json; charset=utf-8") -> list[tuple[str, str]]:
    settings = get_settings()
    headers = [
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
    ]
    if settings.secure_headers:
        headers.extend(
            [
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "DENY"),
                ("Referrer-Policy", "strict-origin-when-cross-origin"),
            ]
        )
    return headers


def response(start_response, status: str, body: bytes, content_type: str = "application/json; charset=utf-8", request_id: str | None = None):
    request_id = request_id or uuid4().hex
    headers = _headers(body, content_type)
    headers.append(("X-Request-ID", request_id))
    start_response(status, headers)
    return [body]


def j(start_response, status: str, data: dict, request_id: str | None = None):
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
    return response(start_response, status, body, request_id=request_id)


def static(start_response, path: str, request_id: str):
    requested = unquote(path.lstrip("/")) or "index.html"
    candidate = (FRONTEND / requested).resolve()
    frontend_root = FRONTEND.resolve()
    if frontend_root not in candidate.parents or not candidate.is_file():
        return api_error(start_response, "404 Not Found", "NOT_FOUND", "Resource not found", request_id)
    content_type = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".svg": "image/svg+xml",
        ".json": "application/json; charset=utf-8",
    }.get(candidate.suffix.lower(), "application/octet-stream")
    return response(start_response, "200 OK", candidate.read_bytes(), content_type, request_id)


def _method_not_allowed(start_response, request_id: str):
    return api_error(start_response, "405 Method Not Allowed", "METHOD_NOT_ALLOWED", "Method not allowed", request_id)


def application(environ, start_response):
    request_id = (environ.get("HTTP_X_REQUEST_ID") or uuid4().hex).strip()[:128]
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/") or "/"

    if path in {"/health", "/api/v1/health"}:
        if method != "GET":
            return _method_not_allowed(start_response, request_id)
        if path == "/health":
            return j(start_response, "200 OK", {"status": "ok", "service": SERVICE_NAME}, request_id)
        return j(start_response, "200 OK", {"data": {"status": "ok", "service": SERVICE_NAME, "api_version": API_VERSION}}, request_id)

    if path in {"/ready", "/api/v1/ready"}:
        if method != "GET":
            return _method_not_allowed(start_response, request_id)
        db = check_connection()
        status = "ready" if db else "not_ready"
        http_status = "200 OK" if db else "503 Service Unavailable"
        return j(
            start_response,
            http_status,
            {"data": {"status": status, "dependencies": {"http": "ok", "database": "ok" if db else "unavailable"}}},
            request_id,
        )

    if path == "/api/v1/metadata":
        if method != "GET":
            return _method_not_allowed(start_response, request_id)
        settings = get_settings()
        return j(
            start_response,
            "200 OK",
            {"data": {"service": SERVICE_NAME, "api_version": API_VERSION, "environment": settings.environment}},
            request_id,
        )

    if path.startswith("/api/v1/"):
        return api_error(start_response, "404 Not Found", "NOT_FOUND", "API route not found", request_id)

    if method == "GET" and path in {"/", "/app", "/app/"}:
        return static(start_response, "index.html", request_id)
    if method == "GET" and path == "/landing.html":
        return static(start_response, "landing.html", request_id)
    if method == "GET" and path.startswith("/assets/"):
        return static(start_response, path, request_id)
    if method == "GET" and path in {
        "/produit/",
        "/comment-ca-marche/",
        "/services/",
        "/tarifs/",
        "/ressources/",
        "/contact/",
        "/analyse-avis-google/",
        "/ia-et-controle-humain/",
        "/securite/",
        "/confidentialite/",
    }:
        return static(start_response, "index.html", request_id)

    return api_error(start_response, "404 Not Found", "NOT_FOUND", "Resource not found", request_id)


app = application
