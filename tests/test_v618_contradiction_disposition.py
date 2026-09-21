import io, json
from src.api_server import ReviewDefenseAPI

def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)

def setup():
    app=ReviewDefenseAPI(); app.seed_user(organization_id='org-a',email='a@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'a@example.com','password':'StrongPass123!'})
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'La facture était de 60 euros.','rating':1,'published_at':'2026-09-20'},login['access_token'])
    _,created=call(app,'POST','/v1/cases',{'review_id':'r1'},login['access_token'])
    cid=created['case']['case_id']
    app.store.contradictions[('org-a',cid)]=[{'contradiction_id':'ctr_test','case_id':cid,'claim_id':'claim-1','evidence_ids':['e1'],'key':'amount:eur','kind':'AMOUNT','claim_value':'60','evidence_values':['90'],'description':'conflict','confidence':0.99,'requires_human_review':True}]
    return app,login['access_token'],cid

def test_disposition_is_human_and_audited():
    app,t,cid=setup(); status,res=call(app,'POST',f'/v1/cases/{cid}/contradictions/ctr_test/disposition',{'status':'EXPLAINED','rationale':'Invoice correction documented by analyst.'},t)
    assert status=='200 OK'; assert res['requires_human_review'] is True
    assert app.store.contradiction_dispositions[('org-a','ctr_test')]['status']=='EXPLAINED'
    assert any(a['action']=='CONTRADICTION_DISPOSITIONED' for a in app.store.audit)

def test_disposition_requires_rationale():
    app,t,cid=setup(); status,_=call(app,'POST',f'/v1/cases/{cid}/contradictions/ctr_test/disposition',{'status':'FALSE_POSITIVE'},t)
    assert status=='422 Unprocessable Entity'

def test_disposition_is_tenant_scoped():
    app,t,cid=setup(); app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    status,_=call(app,'POST',f'/v1/cases/{cid}/contradictions/ctr_test/disposition',{'status':'EXPLAINED','rationale':'x'},login['access_token'])
    assert status=='404 Not Found'

def test_get_contradictions_exposes_disposition_without_auto_resolution():
    app,t,cid=setup(); call(app,'POST',f'/v1/cases/{cid}/contradictions/ctr_test/disposition',{'status':'NEEDS_MORE_EVIDENCE','rationale':'Need original invoice.'},t)
    status,res=call(app,'GET',f'/v1/cases/{cid}/contradictions',token=t)
    assert status=='200 OK'; assert res['contradictions'][0]['disposition']['status']=='NEEDS_MORE_EVIDENCE'; assert res['requires_human_review'] is True
