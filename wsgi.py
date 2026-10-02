"""Single production WSGI entrypoint for the API and public/client frontend.

The API remains available under /v1/* and operational endpoints stay at their
canonical root paths. Public SEO pages are rendered by src.seo_site; the
existing workspace shell continues to serve authenticated client/admin flows.
"""
from pathlib import Path
from urllib.parse import parse_qs
import mimetypes

from src import seo_site
from src.api_server import create_app

_application = create_app()

ROOT = Path(__file__).resolve().parent
FRONTEND_ROOT = (ROOT / "frontend").resolve()
_API_PREFIXES = ("/v1/",)
_NON_API_PATHS = {"/health", "/healthz", "/metrics", "/ready"}
_FRONTEND_FILES = {
    "/index.html", "/styles.css", "/script.js",
    "/workspace.css", "/workspace.js", "/workspace.html",
}
_ROUTE_PAGES = {
    "/client": "workspace.html",
    "/client/": "workspace.html",
    "/admin": "workspace.html",
    "/admin/": "workspace.html",
    "/app": "workspace.html",
    "/app/": "workspace.html",
    "/connexion": "workspace.html",
    "/inscription": "workspace.html",
    "/verify-email": "workspace.html",
    "/reset-password": "workspace.html",
    "/accept-invitation": "workspace.html",
    "/conformite/": "index.html",
    "/mentions-legales/": "index.html",
    "/confidentialite/": "index.html",
    "/cgv/": "index.html",
    "/cgu/": "index.html",
    "/cookies/": "index.html",
    "/securite/": "index.html",
    "/conservation-donnees/": "index.html",
    "/droits-rgpd/": "index.html",
    "/violation-donnees/": "index.html",
    "/sous-traitants/": "index.html",
    "/ia-et-controle-humain/": "index.html",
    "/about": "about.html",
    "/about/": "about.html",
    "/about.html": "about.html",
}
_QUERY_REDIRECTS = {
    "features": "/produit/",
    "product": "/produit/",
    "how": "/comment-ca-marche/",
    "pricing": "/tarifs/",
    "resources": "/ressources/",
}
_PATH_REDIRECTS = {
    "/login": "/app",
    "/services": "/services/",
    "/services.html": "/services/",
    "/fonctionnement": "/comment-ca-marche/",
    "/fonctionnement.html": "/comment-ca-marche/",
    "/resources": "/ressources/",
    "/resources/": "/ressources/",
    "/resources.html": "/ressources/",
    "/ressources": "/ressources/",
    "/tarif": "/tarifs/",
    "/tarif/": "/tarifs/",
    "/tarif.html": "/tarifs/",
    "/contact": "/contact/",
    "/produit": "/produit/",
    "/tarifs": "/tarifs/",
    "/comment-ca-marche": "/comment-ca-marche/",
    "/google-refuse-de-supprimer-mon-faux-avis-que-faire/": "/google-refuse-de-supprimer-mon-faux-avis/",
    "/pourquoi-mon-avis-google-reste-en-ligne-conversationnel/": "/pourquoi-mon-avis-google-reste-en-ligne/",
}


def _redirect(location, start_response):
    start_response(
        "301 Moved Permanently",
        [
            ("Location", location),
            ("Content-Length", "0"),
            ("Cache-Control", "no-store"),
        ],
    )
    return [b""]


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


def _seo_response(path, start_response):
    rendered = seo_site.render(path)
    if rendered is None:
        return None
    status, headers, body = rendered
    phrases = {200: "OK", 301: "Moved Permanently", 404: "Not Found"}
    response_headers = list(headers.items())
    response_headers.append(("Content-Length", str(len(body))))
    response_headers.append(("X-Content-Type-Options", "nosniff"))
    response_headers.append(("X-Frame-Options", "DENY"))
    response_headers.append(("Referrer-Policy", "strict-origin-when-cross-origin"))
    start_response(f"{status} {phrases.get(status, 'OK')}", response_headers)
    return [body]


def _frontend_response(path, start_response):
    if path == "/":
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
            ("Cache-Control", "no-cache" if candidate.name in {"index.html", "workspace.html"} else "public, max-age=3600"),
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
        query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
        legacy_page = query.get("page", [None])[0]
        if path == "/" and legacy_page in _QUERY_REDIRECTS:
            return _redirect(_QUERY_REDIRECTS[legacy_page], start_response)

        redirect = _PATH_REDIRECTS.get(path)
        if redirect:
            return _redirect(redirect, start_response)

        # Canonical public SEO pages and the SEO network take precedence over
        # legacy static-page aliases so only one public URL family is indexed.
        if seo_site.is_seo_path(path):
            response = _seo_response(path, start_response)
            if response is not None:
                return response

        frontend = _frontend_response(path, start_response)
        if frontend is not None:
            return frontend

    if not (path.startswith(_API_PREFIXES) or path in _NON_API_PATHS):
        return _json_404(start_response)

    return _application(environ, start_response)
