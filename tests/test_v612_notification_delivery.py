import json, io
from types import SimpleNamespace
import pytest
from src.notification_delivery import DeliveryError, deliver, validate_webhook_target
from src.api_server import ReviewDefenseAPI
from src.notification_outbox import create_notification


def n(channel, target):
    return create_notification(organization_id="org-a", case_id="case-1", level="DUE", channel=channel, target=target, subject="Alert", body="Review needed", actor_id="u1")


def test_webhook_rejects_private_resolution():
    def resolver(*args, **kwargs): return [(None,None,None,None,("10.0.0.2",0))]
    with pytest.raises(DeliveryError): validate_webhook_target("https://example.com/hook", resolver=resolver)


def test_email_delivery_uses_smtp_transport():
    sent=[]
    class SMTP:
        def __init__(self,*a,**k): pass
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def starttls(self): pass
        def login(self,*a): pass
        def send_message(self,msg): sent.append(msg)
    r=deliver(n("EMAIL","ops@example.com"), email_config={"host":"smtp.example.com","port":587,"sender":"rd@example.com"}, smtp_factory=SMTP)
    assert r.delivered and sent[0]["To"] == "ops@example.com"


def test_webhook_delivery_uses_injected_opener():
    seen=[]
    class Resp:
        status=204
        def __enter__(self): return self
        def __exit__(self,*a): pass
    def opener(req, timeout=8): seen.append((req.full_url, req.get_method(), req.get_header("Content-type"))); return Resp()
    def resolver(*args, **kwargs): return [(None,None,None,None,("93.184.216.34",0))]
    r=deliver(n("WEBHOOK","https://example.com/hook"), opener=opener, resolver=resolver)
    assert r.delivered and seen[0][0].startswith("https://example.com/")


def test_in_app_delivery_is_local_only():
    r=deliver(n("IN_APP","user-1"))
    assert r.delivered and r.provider == "internal"

def test_api_delivery_is_owner_controlled_and_audited(monkeypatch):
    import io, json
    from src.api_server import ReviewDefenseAPI
    app=ReviewDefenseAPI(delivery_func=lambda notification, email_config: SimpleNamespace(channel=notification.channel, delivered=True, provider="test", detail="ok"))
    app.seed_user(organization_id="org-a",email="a@example.com",password="StrongPass123!",role="OWNER")
    def call(method,path,body=None,token=None):
        raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
        if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
        out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)
    _,login=call("POST","/v1/auth/login",{"email":"a@example.com","password":"StrongPass123!"})
    t=login["access_token"]
    call("POST","/v1/reviews",{"review_id":"r1","text":"bad","rating":1,"published_at":"x"},t)
    _,case=call("POST","/v1/cases",{"review_id":"r1"},t); cid=case["case"]["case_id"]
    from src.escalation_workflow import Escalation
    app.store.escalations[("org-a",cid,"DUE")]=Escalation(cid,"DUE","SLA breached")
    _,created=call("POST",f"/v1/escalations/{cid}/notify",{"channel":"IN_APP","target":"user-1"},t)
    s,res=call("POST",f"/v1/notifications/{created['notification']['notification_id']}/deliver",{},t)
    assert s=="200 OK" and res["notification"]["status"]=="SENT"
    assert any(a["action"]=="ESCALATION_NOTIFICATION_DELIVERED" for a in app.store.audit)
