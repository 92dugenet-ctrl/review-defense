from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
STARTUP = (ROOT / "scripts" / "start_production.sh").read_text(encoding="utf-8")
COMPOSE_BASE = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
COMPOSE_STAGING = (ROOT / "docker-compose.staging.yml").read_text(encoding="utf-8")
COMPOSE_PRODUCTION = (ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")


def test_container_startup_enforces_production_environment_when_unspecified():
    assert 'export REVIEW_DEFENSE_ENV="${REVIEW_DEFENSE_ENV:-production}"' in STARTUP
    assert "exec gunicorn" in STARTUP
    assert "wsgi:app" in STARTUP
    assert "scripts/start_production.sh" in DOCKERFILE


def test_container_startup_keeps_runtime_port():
    assert "0.0.0.0:${PORT:-8080}" in STARTUP


def test_compose_environments_use_the_image_startup_contract():
    # Compose must not override the Dockerfile CMD: it runs production checks,
    # applies migrations, and starts the same WSGI application in every mode.
    for compose in (COMPOSE_BASE, COMPOSE_STAGING, COMPOSE_PRODUCTION):
        assert "command:" not in compose
    assert "REVIEW_DEFENSE_ENV: development" in COMPOSE_BASE
    assert "REVIEW_DEFENSE_ENV: production" in COMPOSE_STAGING
    assert "REVIEW_DEFENSE_ENV: production" in COMPOSE_PRODUCTION


def test_production_compose_keeps_existing_published_ports_and_proxy():
    assert '"80:80", "443:443"' in COMPOSE_STAGING
    assert '"${PORT:-8080}:8080"' in COMPOSE_PRODUCTION
    assert 'TRUST_PROXY: "true"' in COMPOSE_STAGING
    assert 'TRUST_PROXY: "true"' in COMPOSE_PRODUCTION
