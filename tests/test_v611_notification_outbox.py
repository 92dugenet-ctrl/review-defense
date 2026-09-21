import io, json
from src.api_server import ReviewDefenseAPI

def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)

def setup(role="OWNER"):
    app=ReviewDefenseAPI(); app.seed_user(organization_id="org-a",email="a@example.com",password="StrongPass123!",role=role)
    _,login=call(app,"POST","/v1/auth/login",{"email":"a@example.com","password":"StrongPass123!"})
    return app,login["access_token"]

def make_escalation(app,t):
    call(app,"POST","/v1/reviews",{"review_id":"r1","text":"bad","rating":1,"published_at":"x"},t)
    _,case=call(app,"POST","/v1/cases",{"review_id":"r1"},t); cid=case["case"]["case_id"]
    from src.escalation_workflow import Escalation
    app.store.escalations[("org-a",cid,"DUE")]=Escalation(cid,"DUE","SLA breached")
    return cid

def test_owner_can_queue_escalation_notification():
    app,t=setup(); cid=make_escalation(app,t)
    status,res=call(app,"POST",f"/v1/escalations/{cid}/notify",{"level":"DUE","channel":"EMAIL","target":"ops@example.com"},t)
    assert status=="201 Created" and res["notification"]["status"]=="PENDING"
    assert any(a["action"]=="ESCALATION_NOTIFICATION_QUEUED" for a in app.store.audit)

def test_notification_is_deduplicated():
    app,t=setup(); cid=make_escalation(app,t); body={"level":"DUE","channel":"EMAIL","target":"ops@example.com"}
    s1,r1=call(app,"POST",f"/v1/escalations/{cid}/notify",body,t); s2,r2=call(app,"POST",f"/v1/escalations/{cid}/notify",body,t)
    assert s1=="201 Created" and s2=="200 OK" and r2["deduplicated"] is True
    assert len(app.store.notifications)==1

def test_notification_lifecycle_is_human_controlled():
    app,t=setup(); cid=make_escalation(app,t)
    _,created=call(app,"POST",f"/v1/escalations/{cid}/notify",{"channel":"IN_APP","target":"user-1"},t); nid=created["notification"]["notification_id"]
    s,res=call(app,"POST",f"/v1/notifications/{nid}/mark-sent",token=t)
    assert s=="200 OK" and res["notification"]["status"]=="SENT" and res["notification"]["sent_by"]

def test_pending_notification_can_be_cancelled():
    app,t=setup(); cid=make_escalation(app,t)
    _,created=call(app,"POST",f"/v1/escalations/{cid}/notify",{"channel":"IN_APP","target":"user-1"},t); nid=created["notification"]["notification_id"]
    s,res=call(app,"POST",f"/v1/notifications/{nid}/cancel",token=t)
    assert s=="200 OK" and res["notification"]["status"]=="CANCELLED"

def test_analyst_cannot_queue_external_notification():
    app,t=setup("ANALYST"); cid=make_escalation(app,t)
    s,_=call(app,"POST",f"/v1/escalations/{cid}/notify",{"channel":"EMAIL","target":"ops@example.com"},t)
    assert s.startswith("403 ")

def test_notifications_are_tenant_isolated():
    app,t=setup(); cid=make_escalation(app,t); _,created=call(app,"POST",f"/v1/escalations/{cid}/notify",{"channel":"IN_APP","target":"user-1"},t); nid=created["notification"]["notification_id"]
    app.seed_user(organization_id="org-b",email="b@example.com",password="StrongPass123!",role="OWNER")
    _,login=call(app,"POST","/v1/auth/login",{"email":"b@example.com","password":"StrongPass123!"})
    s,_=call(app,"POST",f"/v1/notifications/{nid}/cancel",token=login["access_token"])
    assert s.startswith("404 ")
