import os
from email.message import EmailMessage
from tests.test_v60_api import call
from src.api_server import create_app
from src.production_config import ProductionConfig
from src.recovery_email import SMTPConfig, build_recovery_link, send_recovery_email, RecoveryEmailError

class FakeSMTP:
    messages=[]
    def __init__(self, host, port, timeout=10): self.host=host; self.port=port; self.timeout=timeout
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def starttls(self): pass
    def login(self,u,p): pass
    def send_message(self,msg): self.messages.append(msg)

def test_v625_recovery_email_contains_one_time_link_without_exposing_token_in_response(monkeypatch):
    cfg=ProductionConfig(environment="development", recovery_email_enabled=True, smtp_host="smtp.test", smtp_sender="security@example.com", public_base_url="https://app.example")
    app=create_app(config=cfg)
    app.seed_user(organization_id="org-email", email="user@example.com", password="old password 123")
    sent=[]
    def fake_send(**kwargs): sent.append(kwargs)
    monkeypatch.setattr("src.api_server.send_recovery_email", fake_send)
    status,data=call(app,"POST","/v1/auth/recovery/request",{"organization_id":"org-email","email":"user@example.com"})
    assert status==200 and "recovery_token" not in data
    assert len(sent)==1 and sent[0]["recipient"]=="user@example.com"

def test_v625_email_helpers_build_safe_link_and_send():
    raw="abc/def?token"
    link=build_recovery_link("https://app.example/", "org id", raw)
    assert link.startswith("https://app.example/reset-password?") and "org%20id" in link
    FakeSMTP.messages=[]
    send_recovery_email(recipient="user@example.com", organization_id="org", token=raw, base_url="https://app.example", config=SMTPConfig("smtp.test", sender="security@example.com"), smtp_factory=FakeSMTP)
    assert len(FakeSMTP.messages)==1
    msg=FakeSMTP.messages[0]
    assert isinstance(msg, EmailMessage) and msg["To"]=="user@example.com" and "Password reset" in msg["Subject"]
    assert "abc/def?token" not in msg.get_content()
    assert "abc/def%3Ftoken" in msg.get_content()

def test_v625_verification_endpoint_is_single_use_and_login_can_require_verification():
    cfg=ProductionConfig(environment="development", recovery_email_enabled=False, require_email_verification=False)
    app=create_app(config=cfg)
    user=app.seed_user(organization_id="org-ver", email="v@example.com", password="password 12345")
    app.config = ProductionConfig(environment="development", recovery_email_enabled=False, require_email_verification=True)
    app.store.email_verified[user.user_id]=False
    raw, _ = app._issue_email_verification(user)
    status,_=call(app,"POST","/v1/auth/login",{"organization_id":"org-ver","email":"v@example.com","password":"password 12345"})
    assert status==403
    status,out=call(app,"POST","/v1/auth/email-verification/verify",{"organization_id":"org-ver","verification_token":raw})
    assert status==200 and out["status"]=="email_verified"
    status,_=call(app,"POST","/v1/auth/email-verification/verify",{"organization_id":"org-ver","verification_token":raw})
    assert status==400
    status,login=call(app,"POST","/v1/auth/login",{"organization_id":"org-ver","email":"v@example.com","password":"password 12345"})
    assert status==200 and login["access_token"]

def test_v625_production_email_configuration_is_validated():
    cfg=ProductionConfig(environment="production", host="0.0.0.0", database_dsn="postgresql://db", recovery_email_enabled=True)
    try:
        cfg.validate_startup()
        assert False
    except ValueError as exc:
        assert "SMTP_HOST" in str(exc)
    cfg=ProductionConfig(environment="production", host="0.0.0.0", database_dsn="postgresql://db", recovery_email_enabled=True, smtp_host="smtp.test", smtp_sender="security@example.com", public_base_url="http://app.example")
    try:
        cfg.validate_startup(); assert False
    except ValueError as exc:
        assert "HTTPS" in str(exc)

def test_v625_health_version():
    app=create_app(config=ProductionConfig(environment="development"))
    status,data=call(app,"GET","/health")
    assert status==200 and data["version"]=="6.39"
