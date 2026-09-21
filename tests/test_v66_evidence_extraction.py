import io, json
from src.api_server import ReviewDefenseAPI
from src.evidence_extraction import extract_text_fact_suggestions

def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)

def setup():
    app=ReviewDefenseAPI(); app.seed_user(organization_id='org-a',email='a@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'a@example.com','password':'StrongPass123!'})
    return app,login['access_token']

def test_text_extraction_is_unverified_and_deterministic():
    content=b'Facture: 60 euros\nDuree: 2 heures\nDate: 20/09/2026\n'
    a=extract_text_fact_suggestions(evidence_id='e1',content=content,content_type='text/plain')
    b=extract_text_fact_suggestions(evidence_id='e1',content=content,content_type='text/plain')
    assert [x.suggestion_id for x in a]==[x.suggestion_id for x in b]
    assert len(a)==3 and all(not x.verified for x in a)

def test_api_extracts_only_readable_text_and_never_verifies():
    app,t=setup()
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'On m\'a facture 50 euros.','rating':1,'published_at':'2026-09-20'},t)
    _,created=call(app,'POST','/v1/cases',{'review_id':'r1'},t); cid=created['case']['case_id']
    import base64
    status,up=call(app,'POST','/v1/evidence',{'case_id':cid,'filename':'receipt.txt','content_type':'text/plain','content_base64':base64.b64encode(b'60 euros').decode()},t)
    eid=up['evidence']['evidence_id']; status,res=call(app,'POST',f'/v1/cases/{cid}/extract-facts',{},t)
    assert status=='200 OK' and res['count']==1 and res['verified'] is False
    assert res['suggestions'][0]['key']=='amount:eur'

def test_binary_or_pdf_is_not_interpreted():
    assert extract_text_fact_suggestions(evidence_id='e1',content=b'60 euros',content_type='application/pdf')==()

def test_extraction_is_tenant_scoped():
    app,t=setup(); call(app,'POST','/v1/reviews',{'review_id':'r2','text':'x','rating':1,'published_at':'x'},t); _,c=call(app,'POST','/v1/cases',{'review_id':'r2'},t); cid=c['case']['case_id']
    import base64
    call(app,'POST','/v1/evidence',{'case_id':cid,'filename':'x.txt','content_type':'text/plain','content_base64':base64.b64encode(b'60 euros').decode()},t)
    app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST'); _,l=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    status,_=call(app,'POST',f'/v1/cases/{cid}/extract-facts',{},l['access_token']); assert status=='404 Not Found'
