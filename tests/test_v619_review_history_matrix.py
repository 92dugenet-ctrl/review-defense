import io,json
from src.api_server import ReviewDefenseAPI

def call(app,method,path,body=None,token=None):
    raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
    if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
    out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)

def setup():
    app=ReviewDefenseAPI(); app.seed_user(organization_id='org-a',email='a@example.com',password='StrongPass123!',role='ANALYST')
    _,login=call(app,'POST','/v1/auth/login',{'email':'a@example.com','password':'StrongPass123!'})
    call(app,'POST','/v1/reviews',{'review_id':'r1','text':'Le service a coûté 60 euros.','rating':1,'published_at':'2026-09-20'},login['access_token'])
    _,created=call(app,'POST','/v1/cases',{'review_id':'r1'},login['access_token']); cid=created['case']['case_id']
    from src.review_workspace import extract_claims
    claim_id=extract_claims(app.store.reviews[('org-a','r1')])[0].claim_id
    app.store.contradictions[('org-a',cid)]=[{'contradiction_id':'ctr_test','case_id':cid,'claim_id':claim_id,'evidence_ids':['e1'],'key':'amount:eur','kind':'AMOUNT','claim_value':'60','evidence_values':['90'],'description':'conflict','confidence':0.99,'requires_human_review':True}]
    app.store.evidence[('org-a','e1')]={'evidence_id':'e1','case_id':cid,'sha256':'abc','verified':True,'source':'invoice'}
    return app,login['access_token'],cid

def test_disposition_history_is_append_only():
    app,t,cid=setup(); path=f'/v1/cases/{cid}/contradictions/ctr_test/disposition'
    call(app,'POST',path,{'status':'NEEDS_MORE_EVIDENCE','rationale':'Need source.'},t)
    call(app,'POST',path,{'status':'EXPLAINED','rationale':'Correction verified.'},t)
    st,res=call(app,'GET',f'/v1/cases/{cid}/contradictions/ctr_test/history',token=t)
    assert st=='200 OK' and res['count']==2 and [x['status'] for x in res['history']]==['NEEDS_MORE_EVIDENCE','EXPLAINED']

def test_history_is_tenant_scoped():
    app,t,cid=setup(); call(app,'POST',f'/v1/cases/{cid}/contradictions/ctr_test/disposition',{'status':'EXPLAINED','rationale':'x'},t)
    app.seed_user(organization_id='org-b',email='b@example.com',password='StrongPass123!',role='ANALYST')
    _,b=call(app,'POST','/v1/auth/login',{'email':'b@example.com','password':'StrongPass123!'})
    st,_=call(app,'GET',f'/v1/cases/{cid}/contradictions/ctr_test/history',token=b['access_token']); assert st=='404 Not Found'

def test_evidence_matrix_is_read_only_and_human_gated():
    app,t,cid=setup(); st,res=call(app,'GET',f'/v1/cases/{cid}/evidence-matrix',token=t)
    assert st=='200 OK' and res['count']==1 and res['matrix'][0]['status']=='CONTRADICTION' and res['requires_human_review'] is True

def test_evidence_matrix_does_not_clear_contradiction_after_disposition():
    app,t,cid=setup(); call(app,'POST',f'/v1/cases/{cid}/contradictions/ctr_test/disposition',{'status':'FALSE_POSITIVE','rationale':'Mismatch in reference number.'},t)
    st,res=call(app,'GET',f'/v1/cases/{cid}/evidence-matrix',token=t)
    assert st=='200 OK' and res['matrix'][0]['status']=='CONTRADICTION'
