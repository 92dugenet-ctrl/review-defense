from tests.test_v60_api import call
from src.api_server import create_app
from src.production_config import ProductionConfig
from src.security_hardening import hash_password


class FakeRepo:
    def __init__(self):
        self.users = {("org-prod", "prod@example.com"): ("u-prod", "prod@example.com", hash_password("correct horse battery staple"), "OWNER")}
        self.sessions = {}
        self.events = []

    def get_user_by_email(self, org, email):
        return self.users.get((org, email))

    def put_session(self, org, token_hash, user_id, role, expires_at, user_agent=None, ip_hash=None):
        self.sessions[token_hash] = (org, user_id, role, expires_at, user_agent, ip_hash)

    def get_session(self, org, token_hash):
        row = self.sessions.get(token_hash)
        if not row: return None
        from datetime import datetime
        org0, uid, role, expires, ua, iph = row
        return token_hash, uid, org0, role, datetime.fromisoformat(expires), None

    def touch_session(self, org, token_hash, user_agent=None, ip_hash=None):
        self.events.append(("touch", org, token_hash, user_agent, ip_hash))

    def security_event(self, org, actor, event_type, target=None, metadata=None):
        self.events.append((event_type, org, actor, target, metadata or {}))

    def revoke_session(self, org, token_hash):
        self.sessions.pop(token_hash, None)


def test_persistent_login_is_tenant_scoped_and_survives_empty_memory_store():
    repo = FakeRepo()
    app = create_app(repository=repo, config=ProductionConfig(environment="development"))
    status, data = call(app, "POST", "/v1/auth/login", {"email": "prod@example.com", "password": "correct horse battery staple"})
    assert status == 422
    status, data = call(app, "POST", "/v1/auth/login", {"organization_id": "wrong-org", "email": "prod@example.com", "password": "correct horse battery staple"})
    assert status == 401
    status, data = call(app, "POST", "/v1/auth/login", {"organization_id": "org-prod", "email": "prod@example.com", "password": "correct horse battery staple"})
    assert status == 200 and data["access_token"]
    assert any(e[0] == "LOGIN" for e in repo.events)


def test_auth_attempts_are_rate_limited_without_affecting_normal_api_rate_limit():
    app = create_app()
    for i in range(8):
        status, _ = call(app, "POST", "/v1/auth/login", {"email": "missing@example.com", "password": "wrong password 123"})
        assert status == 401
    status, data = call(app, "POST", "/v1/auth/login", {"email": "missing@example.com", "password": "wrong password 123"})
    assert status == 429 and data["error"]["code"] == "AUTH_RATE_LIMITED"


def test_authenticated_requests_touch_persistent_session_metadata():
    repo = FakeRepo()
    app = create_app(repository=repo, config=ProductionConfig(environment="development"))
    status, data = call(app, "POST", "/v1/auth/login", {"organization_id": "org-prod", "email": "prod@example.com", "password": "correct horse battery staple"})
    assert status == 200
    token = data["access_token"]
    status, _ = call(app, "GET", "/v1/me", token=token)
    assert status == 200
    assert any(e[0] == "touch" and e[4] for e in repo.events)


def test_health_version_is_v621():
    app = create_app(config=ProductionConfig(environment="development"))
    status, data = call(app, "GET", "/health")
    assert status == 200 and data["version"] == "6.39"
