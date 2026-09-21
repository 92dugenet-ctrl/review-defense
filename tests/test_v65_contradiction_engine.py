import io, json
from src.api_server import ReviewDefenseAPI
from src.contradiction_engine import EvidenceFact, detect_contradictions
from src.review_workspace import ReviewClaim


def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode()
    env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}
    def sr(status, headers): out.update(status=status,headers=headers)
    data=b"".join(app(env,sr)); return out["status"], json.loads(data)


def setup():
    app=ReviewDefenseAPI(); app.seed_user(organization_id="org-a",email="a@example.com",password="StrongPass123!",role="ANALYST")
    _, login=call(app,"POST","/v1/auth/login",{"email":"a@example.com","password":"StrongPass123!"})
    return app, login["access_token"]


def test_engine_detects_only_verified_conflicting_fact():
    claim=ReviewClaim("r-cl1", "On m'a facturé 50 euros.", "FACTUAL")
    facts=(EvidenceFact("e1","amount:eur","AMOUNT","60",verified=True), EvidenceFact("e2","amount:eur","AMOUNT","50",verified=True), EvidenceFact("e3","amount:eur","AMOUNT","90",verified=False))
    findings=detect_contradictions(organization_id="org-a",case_id="c1",claims=(claim,),evidence_facts=facts)
    assert len(findings)==1
    assert findings[0].evidence_ids==("e1",)
    assert findings[0].requires_human_review is True


def test_api_verifies_facts_then_finds_contradiction_and_exposes_it_in_workspace():
    app,t=setup()
    assert call(app,"POST","/v1/reviews",{"review_id":"r1","text":"On m'a facturé 50 euros.","rating":1,"published_at":"2026-09-20T10:00:00Z"},t)[0]=="201 Created"
    _, created=call(app,"POST","/v1/cases",{"review_id":"r1"},t); cid=created["case"]["case_id"]
    status, up=call(app,"POST","/v1/evidence",{"case_id":cid,"filename":"receipt.txt","content_type":"text/plain","content_base64":"NjAgZXVyb3M=","facts":[{"key":"amount:eur","kind":"AMOUNT","value":"60","source_location":"line 1"}]},t)
    assert status=="201 Created"; eid=up["evidence"]["evidence_id"]
    assert call(app,"POST",f"/v1/evidence/{eid}/verify",token=t)[0]=="200 OK"
    status, facts=call(app,"POST",f"/v1/evidence/{eid}/facts/verify",{"fact_ids":[]},t)
    assert status=="200 OK" and facts["verified_count"]==0
    status, facts=call(app,"POST",f"/v1/evidence/{eid}/facts/verify",{},t)
    assert status=="200 OK" and facts["verified_count"]==1
    status, result=call(app,"POST",f"/v1/cases/{cid}/contradictions",{},t)
    assert status=="200 OK" and result["count"]==1 and result["requires_human_review"] is True
    status, ws=call(app,"GET",f"/v1/cases/{cid}/workspace",token=t)
    assert status=="200 OK" and len(ws["workspace"]["contradictions"])==1
    assert ws["requires_human_review"] is True


def test_unverified_fact_does_not_create_finding():
    app,t=setup()
    call(app,"POST","/v1/reviews",{"review_id":"r2","text":"On m'a facturé 50 euros.","rating":1,"published_at":"2026-09-20T10:00:00Z"},t)
    _, created=call(app,"POST","/v1/cases",{"review_id":"r2"},t); cid=created["case"]["case_id"]
    call(app,"POST","/v1/evidence",{"case_id":cid,"filename":"receipt.txt","content_type":"text/plain","content_base64":"NjAgZXVyb3M=","facts":[{"key":"amount:eur","kind":"AMOUNT","value":"60"}]},t)
    status, result=call(app,"POST",f"/v1/cases/{cid}/contradictions",{},t)
    assert status=="200 OK" and result["count"]==0


def test_contradiction_endpoint_is_tenant_isolated():
    app,t=setup()
    call(app,"POST","/v1/reviews",{"review_id":"r3","text":"On m'a facturé 50 euros.","rating":1,"published_at":"x"},t)
    _, created=call(app,"POST","/v1/cases",{"review_id":"r3"},t); cid=created["case"]["case_id"]
    app.seed_user(organization_id="org-b",email="b@example.com",password="StrongPass123!",role="ANALYST")
    _, login=call(app,"POST","/v1/auth/login",{"email":"b@example.com","password":"StrongPass123!"})
    status,_=call(app,"GET",f"/v1/cases/{cid}/contradictions",token=login["access_token"])
    assert status=="404 Not Found"
