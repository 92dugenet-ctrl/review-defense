from __future__ import annotations

import json

from conftest import wsgi_request


def test_health_and_readiness_are_available(app):
    status, headers, body = wsgi_request(app, "/health")
    assert status.startswith("200")
    assert headers["Content-Type"].startswith("application/json")
    assert json.loads(body)["status"] == "ok"
    status, _, body = wsgi_request(app, "/ready")
    assert status.startswith("200")
    assert json.loads(body)["status"] == "ready"


def test_register_then_login_creates_human_account_session(app):
    payload = {"organization_name": "Example SAS", "email": "owner@example.com", "password": "CorrectHorseBatteryStaple!42"}
    status, _, body = wsgi_request(app, "/v1/auth/register", method="POST", body=payload)
    data = json.loads(body)
    assert status.startswith("201")
    assert data["role"] == "OWNER" and data["access_token"]
    status, _, body = wsgi_request(app, "/v1/auth/login", method="POST", body={"email": payload["email"], "password": payload["password"]})
    data = json.loads(body)
    assert status.startswith("200") and data["access_token"]


def test_invalid_login_is_rejected(app):
    payload = {"organization_name": "Example SAS", "email": "owner@example.com", "password": "CorrectHorseBatteryStaple!42"}
    wsgi_request(app, "/v1/auth/register", method="POST", body=payload)
    status, _, body = wsgi_request(app, "/v1/auth/login", method="POST", body={"email": payload["email"], "password": "wrong-password"})
    assert status.startswith("401")
    assert json.loads(body)["error"]["code"] == "AUTH_INVALID"
