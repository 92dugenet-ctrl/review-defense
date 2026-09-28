"""Single production WSGI entrypoint for Review Defense.

Gunicorn enters here once. Compatibility redirects are kept at this boundary;
all normal application, API, static, and SEO handling remains delegated to the
single ReviewDefenseAPI instance.
"""
from urllib.parse import parse_qs

from src.api_server import create_app


_application = create_app()

_LEGACY_QUERY_ROUTES = {
    "features": "/produit/",
    "how": "/comment-ca-marche/",
    "services": "/services/",
    "pricing": "/tarifs/",
    "resources": "/ressources/",
    "contact": "/contact/",
    "google-refuse-de-supprimer-mon-faux-avis-que-faire": "/google-refuse-de-supprimer-mon-faux-avis/",
    "pourquoi-mon-avis-google-reste-en-ligne-conversationnel": "/pourquoi-mon-avis-google-reste-en-ligne/",
}

_LEGACY_PATH_ROUTES = {
    "/google-refuse-de-supprimer-mon-faux-avis-que-faire/": "/google-refuse-de-supprimer-mon-faux-avis/",
    "/pourquoi-mon-avis-google-reste-en-ligne-conversationnel/": "/pourquoi-mon-avis-google-reste-en-ligne/",
}


def _redirect(target, start_response):
    start_response("301 Moved Permanently", [("Location", target), ("Content-Length", "0")])
    return [b""]


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    query = parse_qs(environ.get("QUERY_STRING", ""))

    if path == "/login":
        return _redirect("/app", start_response)

    if path == "/" and query.get("page", [None])[0] in _LEGACY_QUERY_ROUTES:
        return _redirect(_LEGACY_QUERY_ROUTES[query["page"][0]], start_response)

    if path in _LEGACY_PATH_ROUTES:
        return _redirect(_LEGACY_PATH_ROUTES[path], start_response)

    return _application(environ, start_response)
