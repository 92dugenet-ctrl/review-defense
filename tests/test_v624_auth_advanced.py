import os
from tests.test_v60_api import call
from src.api_server import create_app
from src.production_config import ProductionConfig
from src.mfa import totp_code, generate_secret, encrypt_secret


def test_v624_totp_rfc_style_roundtrip():
    secret = generate_secret()
    code = totp_code(secret, 0)
    assert len(code) == 6 and code.isdigit()
    from src.mfa import verify_totp
    assert verify_totp(secret, code, now=0, window=0)
    assert not verify_totp(secret, "000000", now=0, window=0) if code != "000000" else True


def test_v624_mfa_enrollment_requires_confirmation_and_then_login_code():
    os.environ["REVIEW_DEFENSE_DEV_MFA_KEY"] = __import__("cryptography.fernet", fromlist=["Fernet"]).Fernet.generate_key().decode()
    app = create_app(config=ProductionConfig(environment="development"))
    user = app.seed_user(organization_id="org-mfa", email="mfa@example.com", password="correct horse battery staple")
    status, data = call(app, "POST", "/v1/auth/login", {"organization_id":"org-mfa","email":"mfa@example.com","password":"correct horse battery staple"})
    assert status == 200
    token = data["access_token"]
    status, data = call(app, "POST", "/v1/auth/mfa/enroll", {}, token=token)
    assert status == 200 and data["secret"] and data["otpauth_uri"].startswith("otpauth://")
    code = totp_code(data["secret"])
    status, _ = call(app, "POST", "/v1/auth/mfa/confirm", {"code":code}, token=token)
    assert status == 200
    status, _ = call(app, "POST", "/v1/auth/login", {"organization_id":"org-mfa","email":"mfa@example.com","password":"correct horse battery staple"})
    assert status == 401
    status, login = call(app, "POST", "/v1/auth/login", {"organization_id":"org-mfa","email":"mfa@example.com","password":"correct horse battery staple","mfa_code":totp_code(data["secret"])})
    assert status == 200 and login["access_token"]
    os.environ.pop("REVIEW_DEFENSE_DEV_MFA_KEY", None)


def test_v624_recovery_token_is_single_use_and_revokes_sessions():
    os.environ["REVIEW_DEFENSE_EXPOSE_RECOVERY_TOKEN"] = "true"
    app = create_app(config=ProductionConfig(environment="development"))
    app.seed_user(organization_id="org-rec", email="rec@example.com", password="old password 123")
    status, login = call(app, "POST", "/v1/auth/login", {"organization_id":"org-rec","email":"rec@example.com","password":"old password 123"})
    assert status == 200
    status, req = call(app, "POST", "/v1/auth/recovery/request", {"organization_id":"org-rec","email":"rec@example.com"})
    assert status == 200 and req.get("recovery_token")
    token = req["recovery_token"]
    status, out = call(app, "POST", "/v1/auth/recovery/reset", {"organization_id":"org-rec","recovery_token":token,"new_password":"new password 456"})
    assert status == 200
    status, _ = call(app, "GET", "/v1/me", token=login["access_token"])
    assert status == 401
    status, _ = call(app, "POST", "/v1/auth/recovery/reset", {"organization_id":"org-rec","recovery_token":token,"new_password":"another password 789"})
    assert status == 400
    status, login2 = call(app, "POST", "/v1/auth/login", {"organization_id":"org-rec","email":"rec@example.com","password":"new password 456"})
    assert status == 200
    os.environ.pop("REVIEW_DEFENSE_EXPOSE_RECOVERY_TOKEN", None)


def test_v624_recovery_response_does_not_disclose_unknown_account():
    os.environ.pop("REVIEW_DEFENSE_EXPOSE_RECOVERY_TOKEN", None)
    app = create_app(config=ProductionConfig(environment="development"))
    status, data = call(app, "POST", "/v1/auth/recovery/request", {"organization_id":"org-none","email":"nobody@example.com"})
    assert status == 200 and data == {"status":"requested"}


def test_v624_health_version():
    app = create_app(config=ProductionConfig(environment="development"))
    status, data = call(app, "GET", "/health")
    assert status == 200 and data["version"] == "6.39"
