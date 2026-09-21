import io, json
from wsgiref.util import setup_testing_defaults
from src.api_server import create_app
from src.identity import normalize_email, issue_session

def call(app, method, path, body=None, token=None):
    raw=json.dumps(body or {}).encode(); env={}; setup_testing_defaults(env)
    env.update({'REQUEST_METHOD':method, 'PATH_INFO':path, 'wsgi.input':io.BytesIO(raw), 'CONTENT_LENGTH':str(len(raw)), 'REMOTE_ADDR':'test'})
    if token: env['HTTP_AUTHORIZATION']='Bearer '+token
    out={}
    def sr(status,headers): out['status']=int(status.split()[0])
    data=b''.join(app(env,sr)); return out['status'],json.loads(data)

def login(app,email,password='correct horse battery staple'):
    s,d=call(app,'POST','/v1/auth/login',{'email':email,'password':password}); assert s==200; return d['access_token']

def test_identity_validation_and_session_issue():
    assert normalize_email(' A@Example.COM ')=='a@example.com'
    raw,s=issue_session(user_id='u',organization_id='o',role='OWNER',ttl_seconds=60)
    assert raw and s.active()

def test_rotate_invalidates_old_session():
    app=create_app(); app.seed_user(organization_id='o',email='a@example.com',password='correct horse battery staple')
    token=login(app,'a@example.com'); s,d=call(app,'POST','/v1/auth/rotate',token=token); assert s==200
    new=d['access_token']; assert new!=token
    assert call(app,'GET','/v1/me',token=token)[0]==401
    assert call(app,'GET','/v1/me',token=new)[0]==200

def test_password_change_revokes_previous_sessions_and_returns_fresh():
    app=create_app(); app.seed_user(organization_id='o',email='a@example.com',password='correct horse battery staple')
    token=login(app,'a@example.com')
    s,d=call(app,'POST','/v1/auth/change-password',{'current_password':'correct horse battery staple','new_password':'new secure password 123'},token=token)
    assert s==200 and d['access_token']!=token
    assert call(app,'GET','/v1/me',token=token)[0]==401
    fresh=d['access_token']; assert call(app,'GET','/v1/me',token=fresh)[0]==200
    assert login(app,'a@example.com','new secure password 123')

def test_invitation_and_role_management():
    app=create_app(); app.seed_user(organization_id='o',email='owner@example.com',password='correct horse battery staple',role='OWNER')
    app.seed_user(organization_id='o',email='client@example.com',password='correct horse battery staple',role='CLIENT')
    owner=login(app,'owner@example.com')
    s,d=call(app,'POST','/v1/organization/invitations',{'email':'new@example.com','role':'ANALYST'},owner); assert s==201 and d['invitation_token']
    s,d=call(app,'GET','/v1/organization/members',token=owner); assert s==200 and d['count']==2
    target=next(x['user_id'] for x in d['items'] if x['email']=='client@example.com')
    s,d=call(app,'POST',f'/v1/organization/members/{target}/role',{'role':'ANALYST'},owner); assert s==200 and d['role']=='ANALYST'

def test_client_cannot_manage_identity():
    app=create_app(); app.seed_user(organization_id='o',email='c@example.com',password='correct horse battery staple',role='CLIENT')
    token=login(app,'c@example.com')
    assert call(app,'POST','/v1/organization/invitations',{'email':'x@example.com','role':'CLIENT'},token=token)[0]==403
    assert call(app,'POST','/v1/auth/revoke-all',{'user_id':'x'},token=token)[0]==403


def test_invitation_acceptance_is_single_use():
    app=create_app(); app.seed_user(organization_id='o',email='owner@example.com',password='correct horse battery staple',role='OWNER')
    owner=login(app,'owner@example.com')
    s,d=call(app,'POST','/v1/organization/invitations',{'email':'new@example.com','role':'ANALYST'},owner); assert s==201
    token=d['invitation_token']
    s,d=call(app,'POST','/v1/organization/invitations/accept',{'invitation_token':token,'email':'new@example.com','password':'new secure password 123'}); assert s==200
    fresh=d['access_token']; assert call(app,'GET','/v1/me',token=fresh)[0]==200
    assert call(app,'POST','/v1/organization/invitations/accept',{'invitation_token':token,'email':'new@example.com','password':'new secure password 123'})[0]==400

def test_password_change_rejects_weak_password():
    app=create_app(); app.seed_user(organization_id='o',email='a@example.com',password='correct horse battery staple')
    token=login(app,'a@example.com')
    assert call(app,'POST','/v1/auth/change-password',{'current_password':'correct horse battery staple','new_password':'short'},token=token)[0]==422
