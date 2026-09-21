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

def test_sla_pause_preserves_remaining_time():
    now=datetime(2026,9,21,tzinfo=timezone.utc)
    created=(now-timedelta(hours=3)).isoformat(); paused=(now-timedelta(hours=2)).isoformat()
    sla=calculate_sla(priority='CRITICAL',created_at=created,now=now,paused_at=paused,paused_seconds=0)
    assert sla.status=='PAUSED' and sla.paused and sla.remaining_hours==3.0

def test_sla_escalates_after_material_overdue():
    now=datetime(2026,9,21,tzinfo=timezone.utc)
    created=(now-timedelta(hours=6)).isoformat()
    sla=calculate_sla(priority='CRITICAL',created_at=created,now=now)
    assert sla.status=='OVERDUE' and sla.escalation=='CRITICAL'

def test_case_can_pause_and_resume_sla_with_audit():
    app,t=setup(); call(app,'POST','/v1/reviews',{'review_id':'r1','text':'bad','rating':1,'published_at':'x'},t)
    _,c=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=c['case']['case_id']
    status,p=call(app,'POST',f'/v1/cases/{cid}/pause-sla',{'reason':'Waiting for customer evidence'},t)
    assert status=='200 OK' and p['reason']=='Waiting for customer evidence'
    status,s=call(app,'GET',f'/v1/cases/{cid}/sla',token=t)
    assert status=='200 OK' and s['sla']['status']=='PAUSED' and s['sla']['paused'] is True
    status,r=call(app,'POST',f'/v1/cases/{cid}/resume-sla',{},t)
    assert status=='200 OK' and r['sla_paused_seconds'] >= 0
    assert [a['action'] for a in app.store.audit if a['resource']==f'case:{cid}'][-2:] == ['CASE_SLA_PAUSED','CASE_SLA_RESUMED']

def test_cross_tenant_cannot_control_sla():
    app,t=setup(); call(app,'POST','/v1/reviews',{'review_id':'r1','text':'bad','rating':1,'published_at':'x'},t)
    _,c=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=c['case']['case_id']
    app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    status,_=call(app,'POST',f'/v1/cases/{cid}/pause-sla',{'reason':'x'},login['access_token'])
    assert status.startswith('404 ')
