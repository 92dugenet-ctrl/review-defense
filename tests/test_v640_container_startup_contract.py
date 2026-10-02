from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")


def test_container_startup_enforces_production_environment_when_unspecified():
    assert 'export REVIEW_DEFENSE_ENV=\\\"${REVIEW_DEFENSE_ENV:-production}\\\"' in DOCKERFILE
    assert "exec gunicorn" in DOCKERFILE


def test_container_startup_keeps_runtime_port():
    assert "0.0.0.0:${PORT:-8080}" in DOCKERFILE