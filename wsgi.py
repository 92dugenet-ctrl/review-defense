"""Single production WSGI entrypoint for the API and standalone frontend.

The frontend is the static application in the frontend/ directory. The API
remains available under /v1/* and operational endpoints stay at their
canonical root paths.
"""

from pathlib import Path
import mimetypes

from src.api_server import create_app


_application = create_app()

ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = (ROOT / "frontend").resolve()
_API_PREFIXES = ("/v1/",)
_NON_API_PATHS = {"/health", "/healthz", "/metrics", "/ready"}
_FRONTEND_FILES = {"/index.html", "/styles.css", "/script.js"}
_ROUTE_PAGES = {
    "/services": "services.html",
    "/services/": "services.html",
    "/services.html": "services.html",
    "/fonctionnement": "fonctionnement.html",
    "/fonctionnement/": "fonctionnement.html",
    "/fonctionnement.html": "fonctionnement.html",
    "/resources": "resources.html",
    "/resources/": "resources.html",
    "/resources.html": "resources.html",
    "/about": "about.html",
    "/about/": "about.html",
    "/about.html": "about.html",
    "/tarif": "tarif.html",
    "/tarif/": "tarif.html",
    "/tarif.html": "tarif.html",
}


def _redirect(location, start_response):
    body = b""
    start_response(
        "301 Moved Permanently",
        [
            ("Location", location),
            ("Content-Length", "0"),
            ("Cache-Control", "no-store"),
        ],
    )
    return [body]


def _json_404(start_response):
    body = b'{"error":{"code":"NOT_FOUND","message":"resource not found"}}'
    start_response(
        "404 Not Found",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "strict-origin-when-cross-origin"),
        ],
    )
    return [body]


def _frontend_response(path, start_response):
    if path in {"/", "/app", "/app/"}:
        relative = "index.html"
    elif path in _ROUTE_PAGES:
        relative = _ROUTE_PAGES[path]
    elif path in _FRONTEND_FILES:
        relative = path.lstrip("/")
    elif path.startswith("/assets/"):
        relative = path.lstrip("/")
    else:
        return None

    candidate = (FRONTEND_ROOT / relative).resolve()
    try:
        candidate.relative_to(FRONTEND_ROOT)
    except ValueError:
        return _json_404(start_response)

    if not candidate.is_file():
        return _json_404(start_response)

    body = candidate.read_bytes()
    content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
    if content_type.startswith("text/") or content_type in {
        "application/javascript",
        "application/json",
        "image/svg+xml",
    }:
        content_type = f"{content_type}; charset=utf-8"

    start_response(
        "200 OK",
        [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-cache" if candidate.name == "index.html" else "public, max-age=3600"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "strict-origin-when-cross-origin"),
        ],
    )
    return [body]


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/") or "/"
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if method == "GET":
        if path in {"/resources/", "/resources.html"}:
            return _redirect("/resources", start_response)
        frontend = _frontend_response(path, start_response)
        if frontend is not None:
            return frontend

    if not (path.startswith(_API_PREFIXES) or path in _NON_API_PATHS):
        return _json_404(start_response)

    return _application(environ, start_response)
