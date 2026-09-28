import io, json
from src.api_server import ReviewDefenseAPI

def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)

def setup():
    app=ReviewDefenseAPI(); app.seed_user(organization_id='org-a',email='a@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'a@example.com','password':'StrongPass123!'})
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'Excellent mais facture 60 euros.','rating':1,'published_at':'2026-09-20'},login['access_token'])
    _,created=call(app,'POST','/v1/cases',{'review_id':'r1'},login['access_token'])
    return app,login['access_token'],created['case']['case_id']

def test_checklist_is_created_and_not_ready_by_default():
    app,t,cid=setup(); status,res=call(app,'GET',f'/v1/cases/{cid}/review-checklist',token=t)
    assert status=='200 OK'; assert res['items']; assert res['readiness']['ready'] is False

def test_checklist_completion_is_explicit_and_audited():
    app,t,cid=setup(); _,res=call(app,'GET',f'/v1/cases/{cid}/review-checklist',token=t)
    for item in res['items']:
        status,_=call(app,'POST',f'/v1/cases/{cid}/review-checklist',{'code':item['code'],'completed':True,'note':'reviewed'},t); assert status=='200 OK'
    status,res=call(app,'GET',f'/v1/cases/{cid}/review-readiness',token=t)
    assert status=='200 OK' and res['readiness']['ready'] is True
    assert any(a['action']=='CASE_REVIEW_CHECKLIST_UPDATED' for a in app.store.audit)

def test_readiness_never_auto_approves_or_submits():
    app,t,cid=setup(); _,res=call(app,'GET',f'/v1/cases/{cid}/review-readiness',token=t)
    assert res['human_review_required'] is True
    assert app.store.decisions == {} and app.store.submissions == {}

def test_checklist_is_tenant_scoped():
    app,t,cid=setup(); app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    status,_=call(app,'GET',f'/v1/cases/{cid}/review-checklist',token=login['access_token']); assert status=='404 Not Found'
