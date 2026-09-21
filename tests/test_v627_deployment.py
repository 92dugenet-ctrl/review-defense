from pathlib import Path
import os

import pytest

from src.api_server import create_app
from src.deployment import DeploymentConfig, security_headers
from src.production_config import ProductionConfig
from tests.test_v60_api import call

ROOT = Path(__file__).resolve().parents[1]


def test_v627_health_and_security_headers():
    app = create_app(config=ProductionConfig(environment="development", host="127.0.0.1"))
    status, data = call(app, "GET", "/health")
    assert status == 200 and data["version"] == "6.39"


def test_v627_security_headers_include_browser_isolation():
    headers = security_headers(production=False)
    assert "Content-Security-Policy" in headers
    assert "object-src 'none'" in headers["Content-Security-Policy"]
    assert headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert headers["Permissions-Policy"].startswith("camera=()")
    assert "Strict-Transport-Security" not in headers


def test_v627_production_requires_https_and_trusted_proxy():
    cfg = DeploymentConfig("http://example.test", "production", True)
    with pytest.raises(ValueError):
        cfg.validate()
    cfg = DeploymentConfig("https://example.test", "production", False)
    with pytest.raises(ValueError):
        cfg.validate()
    DeploymentConfig("https://example.test", "production", True).validate()


def test_v627_production_config_rejects_http_auth_base_url():
    cfg = ProductionConfig(
        environment="production", host="0.0.0.0", database_dsn="postgresql://x",
        recovery_email_enabled=True, smtp_host="smtp.example", smtp_sender="no-reply@example.com",
        public_base_url="http://example.test",
    )
    with pytest.raises(ValueError):
        cfg.validate_startup(require_database=True)


def test_v627_staging_files_are_present_and_do_not_contain_secrets():
    compose = (ROOT / "docker-compose.staging.yml").read_text()
    caddy = (ROOT / "Caddyfile").read_text()
    checker = (ROOT / "scripts/staging_check.py").read_text()
    assert "postgres:16-alpine" in compose
    assert "caddy:2-alpine" in compose
    assert "reverse_proxy app:8080" in caddy
    assert "STAGING_BASE_URL" in checker
    assert "SMTP_PASSWORD" not in compose
    assert "DATABASE_URL=postgres" not in compose
