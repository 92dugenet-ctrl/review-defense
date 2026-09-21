from src.api_server import create_app
from src.production_config import ProductionConfig
from tests.test_v60_api import call


def test_health_reports_v620_and_security_headers():
    app = create_app(config=ProductionConfig(environment="development", host="127.0.0.1"))
    status, data = call(app, "GET", "/health")
    assert status == 200 and data["version"] == "6.39"


def test_ready_checks_repository_database_when_available():
    class Repo:
        def ping(self): return False
    app = create_app(repository=Repo(), config=ProductionConfig(environment="development", host="127.0.0.1"))
    status, data = call(app, "GET", "/ready")
    assert status == 503 and data["status"] == "not_ready" and data["dependencies"]["database"] == "failed"


def test_ready_does_not_require_database_for_memory_development():
    app = create_app(config=ProductionConfig(environment="development", host="127.0.0.1"))
    status, data = call(app, "GET", "/ready")
    assert status == 200 and data["status"] == "ready"
