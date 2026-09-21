from io import BytesIO
from src.api_server import ReviewDefenseAPI
from src.production_config import ProductionConfig


def env(path="/health", method="GET", headers=None):
    h=headers or {}
    return {"PATH_INFO":path,"REQUEST_METHOD":method,"REMOTE_ADDR":"127.0.0.1","wsgi.input":BytesIO(b""),"CONTENT_LENGTH":"0",**h}


def test_health_is_v640_and_request_id():
    app=ReviewDefenseAPI(config=ProductionConfig(environment="development"))
    captured={}
    body=app(env(), lambda status, headers: captured.update(status=status,headers=dict(headers)))
    assert captured["status"].startswith("200")
    assert captured["headers"]["X-Request-ID"]
    assert b'"version": "6.40"' in body[0]


def test_metrics_exposes_only_aggregate_data():
    app=ReviewDefenseAPI(config=ProductionConfig(environment="development"))
    app(env(), lambda *_: None)
    captured={}
    body=app(env("/metrics"), lambda status, headers: captured.update(status=status,headers=dict(headers)))
    assert captured["status"].startswith("200")
    text=body[0].decode()
    assert "http_requests_total" in text
    assert "password" not in text.lower()


def test_production_metrics_requires_token():
    app=ReviewDefenseAPI(config=ProductionConfig(environment="production", host="0.0.0.0", database_dsn="postgresql://x", trust_proxy=True, public_base_url="https://example.test"))
    captured={}
    body=app(env("/metrics"), lambda status, headers: captured.update(status=status,headers=dict(headers)))
    assert captured["status"].startswith("404")
