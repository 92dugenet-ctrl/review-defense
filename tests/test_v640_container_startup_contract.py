from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
STARTUP = (ROOT / "scripts" / "start_production.sh").read_text(encoding="utf-8")


def test_container_startup_enforces_production_environment_when_unspecified():
    assert 'export REVIEW_DEFENSE_ENV="${REVIEW_DEFENSE_ENV:-production}"' in STARTUP
    assert "exec gunicorn" in STARTUP
    assert "wsgi:app" in STARTUP
    assert "scripts/start_production.sh" in DOCKERFILE


def test_container_startup_keeps_runtime_port():
    assert "0.0.0.0:${PORT:-8080}" in STARTUP
