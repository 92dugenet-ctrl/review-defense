"""Single production WSGI entrypoint for Review Defense.

The public/commercial frontend has been intentionally removed from this
deployment. This boundary exposes the application/API surface only; a new
frontend can be mounted later without changing the backend contract.
"""

from src.api_server import create_app


_application = create_app()

_API_PREFIXES = ("/v1/",)
_NON_API_PATHS = {"/health", "/healthz", "/metrics"}


def _json_404(start_response):
    body = b'{"error":{"code":"NOT_FOUND","message":"frontend removed; API-only deployment"}}'
    start_response(
        "404 Not Found",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ],
    )
    return [body]


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/") or "/"
    if not (path.startswith(_API_PREFIXES) or path in _NON_API_PATHS):
        return _json_404(start_response)
    return _application(environ, start_response)
