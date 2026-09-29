import io
import json
import threading

import pytest

from src.security_hardening import RateLimiter, hash_password, verify_password, hash_token
from src.production_config import ProductionConfig
from src.api_server import ReviewDefenseAPI


def _request(api, path, method="GET", payload=None, headers=None, body_override=None, content_type="application/json", chunked=False):
    raw = body_override if body_override is not None else json.dumps(payload or {}).encode()
    status = []
    response_headers = []

    def start(response_status, response_header_list, exc_info=None):
        status.append(response_status)
        response_headers.extend(response_header_list)

    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": "" if chunked else str(len(raw)),
        "CONTENT_TYPE": content_type,
        "REMOTE_ADDR": "127.0.0.1",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8080",
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(raw),
        "wsgi.input_terminated": chunked,
    }
    for key, value in (headers or {}).items():
        env[f"HTTP_{key.upper().replace('-', '_')}"] = value
    body = b"".join(api(env, start))
    return status[0], dict(response_headers), json.loads(body) if body else None


def test_password_length_is_bounded_and_hashes_are_verifiable():
    with pytest.raises(ValueError):
        hash_password("x" * 257)
    encoded = hash_password("A" * 128)
    assert verify_password("A" * 128, encoded)
    assert not verify_password("A" * 129, encoded)


def test_token_length_is_bounded():
    with pytest.raises(ValueError):
        hash_token("x" * 4097)


def test_rate_limiter_is_thread_safe_and_bounded():
    limiter = RateLimiter(limit=100, window_seconds=60, max_keys=10)
    results = []

    def hit():
        results.append(limiter.allow("same"))

    threads = [threading.Thread(target=hit) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(results)
    assert len(limiter._hits) <= 10
    limited = RateLimiter(limit=1, window_seconds=60)
    assert limited.allow("same")
    assert not limited.allow("same")


def test_production_cannot_disable_security_headers():
    cfg = ProductionConfig(
        environment="production",
        host="0.0.0.0",
        database_dsn="postgresql://example",
        public_base_url="https://review.example",
        secure_headers=False,
    )
    with pytest.raises(ValueError, match="SECURE_HEADERS"):
        cfg.validate_startup()


def test_api_rejects_non_json_mutating_requests():
    api = ReviewDefenseAPI()
    status, _, body = _request(
        api,
        "/v1/auth/register",
        "POST",
        {"email": "x@example.test", "organization_name": "x", "password": "StrongPassword123!"},
        content_type="text/plain",
    )
    assert status == "415 Unsupported Media Type"
    assert body["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_api_rejects_malformed_bearer_headers():
    api = ReviewDefenseAPI()
    status, _, body = _request(api, "/v1/me", headers={"Authorization": "Bearer bad token"})
    assert status == "401 Unauthorized"
    assert body["error"]["code"] == "AUTH_INVALID"


def test_api_limits_chunked_body_without_content_length():
    api = ReviewDefenseAPI()
    raw = b'{"email":"' + b"x" * 1_100_000 + b'"}'
    status, _, body = _request(
        api,
        "/v1/auth/register",
        "POST",
        body_override=raw,
        content_type="application/json",
        chunked=True,
    )
    assert status == "413 Payload Too Large"
    assert body["error"]["code"] == "PAYLOAD_TOO_LARGE"
