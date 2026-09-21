import io, json
from src.api_server import ReviewDefenseAPI


def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode()
    env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}
    def sr(status, headers): out.update(status=status,headers=headers)
    data=b"".join(app(env,sr)); return out["status"], json.loads(data)


def setup():
    app=ReviewDefenseAPI(); u=app.seed_user(organization_id="org-a",email="a@example.com",password="StrongPass123!",role="ANALYST")
    status, login=call(app,"POST","/v1/auth/login",{"email":"a@example.com","password":"StrongPass123!"})
    return app, login["access_token"]


def test_case_workspace_contains_operational_sections_and_tasks():
    app,t=setup()
    assert call(app,"POST","/v1/reviews",{"review_id":"r1","text":"Payez 50 euros ou supprimez mes avis.","rating":1,"published_at":"2026-09-20T10:00:00Z"},t)[0]=="201 Created"
    _, created=call(app,"POST","/v1/cases",{"review_id":"r1"},t); cid=created["case"]["case_id"]
    status, data=call(app,"GET",f"/v1/cases/{cid}/workspace",token=t)
    assert status=="200 OK"
    ws=data["workspace"]
    assert ws["organization_id"]=="org-a"
    assert ws["claims"] and ws["policies"]
    assert data["requires_human_review"] is True
    assert data["evidence_tasks"]


def test_case_workspace_is_tenant_isolated():
    app,t=setup()
    call(app,"POST","/v1/reviews",{"review_id":"r1","text":"bad","rating":1,"published_at":"2026-09-20T10:00:00Z"},t)
    _, created=call(app,"POST","/v1/cases",{"review_id":"r1"},t); cid=created["case"]["case_id"]
    other=app.seed_user(organization_id="org-b",email="b@example.com",password="StrongPass123!",role="ANALYST")
    _, login=call(app,"POST","/v1/auth/login",{"email":"b@example.com","password":"StrongPass123!"})
    status,_=call(app,"GET",f"/v1/cases/{cid}/workspace",token=login["access_token"])
    assert status=="404 Not Found"
