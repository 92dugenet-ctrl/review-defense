import io, json
from datetime import datetime, timezone, timedelta
from src.api_server import ReviewDefenseAPI
from src.review_sla import calculate_sla

def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)

def setup():
    app=ReviewDefenseAPI(); app.seed_user(organization_id='org-a',email='a@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'a@example.com','password':'StrongPass123!'})
    return app,login['access_token']

def test_sla_is_deterministic_and_reports_overdue():
    now=datetime(2026,9,21,tzinfo=timezone.utc)
    created=(now-timedelta(hours=5)).isoformat()
    sla=calculate_sla(priority='CRITICAL',created_at=created,now=now)
    assert sla.sla_hours==4 and sla.status=='OVERDUE' and sla.remaining_hours==-1.0

def test_sla_due_soon_boundary():
    now=datetime(2026,9,21,tzinfo=timezone.utc)
    created=(now-timedelta(hours=3.2)).isoformat()
    assert calculate_sla(priority='CRITICAL',created_at=created,now=now).status=='DUE_SOON'

def test_queue_exposes_sla_and_workload_is_tenant_scoped():
    app,t=setup()
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'bad','rating':1,'published_at':'x'},t)
    _,c=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=c['case']['case_id']
    status,q=call(app,'GET','/v1/review-queue',token=t)
    assert status=='200 OK' and 'sla' in q['items'][0] and q['items'][0]['sla']['status'] in {'ON_TRACK','DUE_SOON','OVERDUE','UNKNOWN'}
    status,w=call(app,'GET','/v1/review-queue/workload',token=t)
    assert status=='200 OK' and w['count']==1 and w['items'][0]['user_id'] is None and w['items'][0]['case_count']==1
    app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    status,w=call(app,'GET','/v1/review-queue/workload',token=login['access_token'])
    assert status=='200 OK' and w['count']==0

def test_assignment_changes_workload_bucket():
    app,t=setup()
    user_id=next(iter(app.store.users))
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'bad','rating':1,'published_at':'x'},t)
    _,c=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=c['case']['case_id']
    call(app,'POST',f'/v1/review-queue/{cid}/claim',{},t)
    status,w=call(app,'GET','/v1/review-queue/workload',token=t)
    assert status=='200 OK' and w['items'][0]['user_id']==user_id and w['items'][0]['case_count']==1
