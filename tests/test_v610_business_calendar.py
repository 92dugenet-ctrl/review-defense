import io, json
from datetime import datetime, timezone
from src.api_server import ReviewDefenseAPI
from src.business_calendar import BusinessCalendar
from src.review_sla import calculate_sla

def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)

def setup(role="OWNER"):
    app=ReviewDefenseAPI(); app.seed_user(organization_id="org-a",email="a@example.com",password="StrongPass123!",role=role)
    _,login=call(app,"POST","/v1/auth/login",{"email":"a@example.com","password":"StrongPass123!"})
    return app,login["access_token"]

def test_business_calendar_skips_weekend():
    cal=BusinessCalendar("UTC",(0,1,2,3,4),9,17,()).validate()
    now=datetime(2026,9,21,12,tzinfo=timezone.utc)
    sla=calculate_sla(priority="CRITICAL",created_at="2026-09-18T16:00:00+00:00",now=now,calendar=cal)
    assert sla.business_calendar is True and sla.calendar_timezone == "UTC"
    assert sla.due_at == "2026-09-21T12:00:00+00:00"

def test_calendar_configuration_is_tenant_scoped():
    app,t=setup()
    status,res=call(app,"POST","/v1/organization/sla-calendar",{"timezone":"UTC","workdays":[0,1,2,3,4],"start_hour":9,"end_hour":17,"holidays":["2026-12-25"]},t)
    assert status=="200 OK" and res["calendar"]["workdays"]==[0,1,2,3,4]
    status,res=call(app,"GET","/v1/organization/sla-calendar",token=t)
    assert status=="200 OK" and res["business_calendar_configured"] is True
    app.seed_user(organization_id="org-b",email="b@example.com",password="StrongPass123!",role="OWNER")
    _,login=call(app,"POST","/v1/auth/login",{"email":"b@example.com","password":"StrongPass123!"})
    status,res=call(app,"GET","/v1/organization/sla-calendar",token=login["access_token"])
    assert status=="200 OK" and res["business_calendar_configured"] is False

def test_overdue_escalation_can_be_acknowledged_and_resolved():
    app,t=setup("ANALYST")
    call(app,"POST","/v1/reviews",{"review_id":"r1","text":"bad","rating":1,"published_at":"x"},t)
    _,case=call(app,"POST","/v1/cases",{"review_id":"r1"},t); cid=case["case"]["case_id"]
    app.store.cases[("org-a",cid)].created_at="2026-09-17T00:00:00+00:00"
    status,res=call(app,"GET","/v1/escalations",token=t)
    assert status=="200 OK"
    # The default 24/7 calendar makes a LOW case overdue after 72h; force priority with a strong policy signal.
    app.store.reviews[("org-a","r1")]=app.store.reviews[("org-a","r1")].__class__("r1","org-a","",None,1,"I was charged 50 euros and never refunded.","x",None,None,"GOOGLE",None)
    status,res=call(app,"GET","/v1/escalations",token=t)
    assert status=="200 OK" and res["count"] >= 1
    esc=res["items"][0]; level=esc["level"]
    status,res=call(app,"POST",f"/v1/escalations/{cid}/acknowledge",{"level":level},t)
    assert status=="200 OK" and res["escalation"]["status"]=="ACKNOWLEDGED"
    status,res=call(app,"POST",f"/v1/escalations/{cid}/resolve",{"level":level},t)
    assert status=="200 OK" and res["escalation"]["status"]=="RESOLVED"
    actions=[a["action"] for a in app.store.audit if a["resource"]==f"case:{cid}"]
    assert "ESCALATION_ACKNOWLEDGED" in actions and "ESCALATION_RESOLVED" in actions

def test_escalation_cross_tenant_isolated():
    app,t=setup("ANALYST")
    call(app,"POST","/v1/reviews",{"review_id":"r1","text":"bad","rating":1,"published_at":"x"},t)
    _,case=call(app,"POST","/v1/cases",{"review_id":"r1"},t); cid=case["case"]["case_id"]
    app.store.escalations[("org-a",cid,"DUE")] = __import__("src.escalation_workflow",fromlist=["Escalation"]).Escalation(cid,"DUE","test")
    app.seed_user(organization_id="org-b",email="b@example.com",password="StrongPass123!",role="ANALYST")
    _,login=call(app,"POST","/v1/auth/login",{"email":"b@example.com","password":"StrongPass123!"})
    status,_=call(app,"POST",f"/v1/escalations/{cid}/acknowledge",{"level":"DUE"},login["access_token"])
    assert status.startswith("404 ")
