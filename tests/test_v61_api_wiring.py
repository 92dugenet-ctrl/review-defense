from src.api_server import create_app

class R:
    def __init__(self): self.calls=[]
    def create_user(self,*a): self.calls.append(('create_user',a)); return ('u1',a[1],a[2],a[3])
    def put_session(self,*a): self.calls.append(('put_session',a))
    def upsert_review(self,*a): self.calls.append(('upsert_review',a))
    def create_case_persistent(self,*a): self.calls.append(('create_case',a)); return ('c','o','r','ANALYZING',None,None,None,None)
    def put_decision(self,*a): self.calls.append(('decision',a))
    def update_case(self,*a,**k): self.calls.append(('case_update',a,k))
    def put_snapshot(self,*a): self.calls.append(('snapshot',a))
    def put_approval(self,*a): self.calls.append(('approval',a))
    def put_submission(self,*a): self.calls.append(('submission',a))

def test_factory_accepts_persistent_repository():
    r=R(); app=create_app(repository=r); assert app.repository is r
