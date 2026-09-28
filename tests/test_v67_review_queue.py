import io, json
from datetime import datetime, timezone, timedelta
from src.api_server import ReviewDefenseAPI
from src.review_queue import score_case, sort_queue

def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)

def setup():
    app=ReviewDefenseAPI(); app.seed_user(organization_id='org-a',email='a@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'a@example.com','password':'StrongPass123!'})
    return app,login['access_token']

def test_priority_score_is_deterministic_and_bounded():
    now=datetime(2026,9,21,tzinfo=timezone.utc)
    item=score_case(case_id='c1',created_at=(now-timedelta(hours=49)).isoformat(),policy_statuses=['STRONG','POSSIBLE'],contradiction_count=2,missing_evidence_count=2,unverified_suggestion_count=3,now=now)
    assert item.priority_score==100 and item.priority=='CRITICAL' and item.requires_human_review
    assert item.age_hours==49.0

def test_queue_orders_highest_risk_first():
    a=score_case(case_id='a',created_at=None,policy_statuses=[],contradiction_count=0,missing_evidence_count=0,unverified_suggestion_count=0)
    b=score_case(case_id='b',created_at=None,policy_statuses=['STRONG'],contradiction_count=1,missing_evidence_count=0,unverified_suggestion_count=0)
    assert [x.case_id for x in sort_queue([a,b])]==['b','a']

def test_review_queue_is_tenant_scoped_and_exposes_reasoning():
    app,t=setup()
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'This business charged 50 euros and never refunded me.','rating':1,'published_at':'2026-09-20'},t)
    _,c=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=c['case']['case_id']
    status,res=call(app,'GET','/v1/review-queue',token=t)
    assert status=='200 OK' and res['count']==1 and res['items'][0]['case_id']==cid
    assert 'reasons' in res['items'][0]
    app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    status,res=call(app,'GET','/v1/review-queue',token=login['access_token'])
    assert status=='200 OK' and res['count']==0

def test_case_can_be_claimed_and_unclaimed_with_audit_event():
    app,t=setup()
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'bad','rating':1,'published_at':'x'},t)
    _,c=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=c['case']['case_id']
    status,res=call(app,'POST',f'/v1/review-queue/{cid}/claim',{},t)
    assert status=='200 OK' and res['assigned_to']==app.store.users[next(iter(app.store.users))].user_id
    status,res=call(app,'POST',f'/v1/review-queue/{cid}/unclaim',{},t)
    assert status=='200 OK' and res['assigned_to'] is None
    assert [x['action'] for x in app.store.audit if x['resource']==f'case:{cid}'][-2:]==['CASE_ASSIGNED','CASE_UNASSIGNED']

def test_cannot_claim_case_from_other_tenant():
    app,t=setup(); call(app,'POST','/v1/reviews',{'review_id':'r1','text':'bad','rating':1,'published_at':'x'},t); _,c=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=c['case']['case_id']
    app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    status,_=call(app,'POST',f'/v1/review-queue/{cid}/claim',{},login['access_token'])
    assert status=='404 Not Found'
