"""Helper d'erreur JSON de l'arborescence backend.api.

Le WSGI de production utilise le traitement d'erreurs de src.api_server.
Ce module est un helper de l'arbre backend et ne constitue pas le handler actif.
"""

from __future__ import annotations

import json
import uuid

from .config import get_settings


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


def api_error(start_response, status: str, code: str, message: str, request_id: str | None = None):
    """Écrit une erreur JSON WSGI avec identifiant de corrélation."""
    request_id = request_id or uuid.uuid4().hex
    body = json.dumps(
        {"error": {"code": code, "message": message}, "request_id": request_id},
        ensure_ascii=False,
    ).encode()
    start_response(status, _headers(body))
    return [body]
