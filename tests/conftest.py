from __future__ import annotations

import io
import json
from typing import Any

import pytest

from src.api_server import MemoryStore, create_app
from src.production_config import ProductionConfig


def wsgi_request(app, path: str, *, method: str = "GET", body: dict[str, Any] | None = None, headers: dict[str, str] | None = None):
    payload = json.dumps(body).encode() if body is not None else b""
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "", "SERVER_NAME": "localhost", "SERVER_PORT": "8080", "SERVER_PROTOCOL": "HTTP/1.1", "wsgi.url_scheme": "http", "wsgi.input": io.BytesIO(payload), "CONTENT_LENGTH": str(len(payload)), "REMOTE_ADDR": "127.0.0.1"}
    for key, value in (headers or {}).items():
        environ["HTTP_" + key.upper().replace("-", "_")] = value
    status, response_headers = [], []
    def start_response(s, h, exc_info=None):
        status.append(s); response_headers.extend(h)
    chunks = app(environ, start_response)
    return status[0], dict(response_headers), b"".join(chunks)


@pytest.fixture
def store():
    return MemoryStore()


@pytest.fixture
def app(store):
    return create_app(store=store, config=ProductionConfig(environment="development"))
