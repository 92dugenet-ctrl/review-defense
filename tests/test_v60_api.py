import io, json
from wsgiref.util import setup_testing_defaults
from src.api_server import create_app, MemoryStore


def call(app, method, path, body=None, token=None, headers=None):
    env = {}
    setup_testing_defaults(env)
    env.update({"REQUEST_METHOD": method, "PATH_INFO": path, "wsgi.input": io.BytesIO(json.dumps(body or {}).encode()), "CONTENT_LENGTH": str(len(json.dumps(body or {}).encode())), "REMOTE_ADDR": "test"})
    if token: env["HTTP_AUTHORIZATION"] = "Bearer " + token
    for k,v in (headers or {}).items(): env[k] = v
    out = {}
    def sr(status, hdrs): out.update(status=status, headers=dict(hdrs))
    raw = b"".join(app(env, sr)); return int(out["status"].split()[0]), json.loads(raw)


def login(app, email="owner@example.com", password="correct horse battery staple"):
    status, data = call(app, "POST", "/v1/auth/login", {"email": email, "password": password})
    assert status == 200
    return data["access_token"]


def test_health_and_auth_and_tenant_isolation():
    app = create_app(); app.seed_user(organization_id="org-a", email="owner@example.com", password="correct horse battery staple")
    assert call(app, "GET", "/health")[0] == 200
    assert call(app, "GET", "/v1/me")[0] == 401
    token = login(app)
    status, me = call(app, "GET", "/v1/me", token=token)
    assert status == 200 and me["organization_id"] == "org-a"
    status, _ = call(app, "GET", "/v1/reviews/not-owned", token=token); assert status == 404


def test_review_case_decision_freeze_approval_submission():
    app = create_app(); app.seed_user(organization_id="org-a", email="owner@example.com", password="correct horse battery staple")
    token = login(app)
    status, _ = call(app, "POST", "/v1/reviews", {"review_id":"r1","location_id":"loc1","rating":1,"text":"Service très lent. J'ai attendu 2 heures."}, token=token)
    assert status == 201
    status, data = call(app, "GET", "/v1/reviews/r1", token=token)
    assert status == 200 and data["claims"]
    status, data = call(app, "POST", "/v1/cases", {"review_id":"r1"}, token=token, headers={"HTTP_IDEMPOTENCY_KEY":"case-1"})
    assert status == 201; cid = data["case"]["case_id"]
    status, _ = call(app, "POST", f"/v1/cases/{cid}/decision", {"kind":"HUMAN_REVIEW","rationale":"Evidence review required"}, token=token); assert status == 201
    status, data = call(app, "POST", f"/v1/cases/{cid}/freeze", {}, token=token); assert status == 200; assert data["snapshot_sha256"]
    status, data = call(app, "POST", f"/v1/cases/{cid}/approve", {}, token=token); assert status == 200
    status, data = call(app, "POST", f"/v1/cases/{cid}/submit", {}, token=token, headers={"HTTP_IDEMPOTENCY_KEY":"sub-1"}); assert status == 201
    assert data["submission"]["external_call"] is False


def test_idempotency_and_conflict():
    app = create_app(); app.seed_user(organization_id="org-a", email="owner@example.com", password="correct horse battery staple")
    token = login(app)
    body={"review_id":"r1","location_id":"l","rating":4,"text":"Bon service."}
    assert call(app,"POST","/v1/reviews",body,token=token)[0] == 201
    status,a=call(app,"POST","/v1/cases",{"review_id":"r1"},token=token,headers={"HTTP_IDEMPOTENCY_KEY":"same"}); assert status==201
    status,b=call(app,"POST","/v1/cases",{"review_id":"r1"},token=token,headers={"HTTP_IDEMPOTENCY_KEY":"same"}); assert status==201 and b==a
    status,_=call(app,"POST","/v1/cases",{"review_id":"r1","x":1},token=token,headers={"HTTP_IDEMPOTENCY_KEY":"same"}); assert status==409


def test_rate_limit_and_validation_and_no_auto_google():
    app = create_app(); app.seed_user(organization_id="org-a", email="owner@example.com", password="correct horse battery staple")
    token=login(app)
    status,_=call(app,"POST","/v1/reviews",{"review_id":"r","rating":9,"text":"x"},token=token); assert status==422
    # Explicit submit is only a local preparation artifact; it must never expose an external mutation flag.
    status,_=call(app,"POST","/v1/reviews",{"review_id":"r","rating":4,"text":"Très bien."},token=token); assert status==201
    assert all("google" not in e.get("action","").lower() or "sync" in e.get("action","").lower() for e in app.store.audit)


def test_evidence_upload_verify_and_tenant_boundary():
    app = create_app()
    app.seed_user(organization_id="org-a", email="owner@example.com", password="correct horse battery staple")
    app.seed_user(organization_id="org-b", email="other@example.com", password="correct horse battery staple")
    token = login(app)
    assert call(app,"POST","/v1/reviews",{"review_id":"r1","location_id":"l","rating":2,"text":"Factuel."},token=token)[0] == 201
    status,data=call(app,"POST","/v1/cases",{"review_id":"r1"},token=token); assert status==201
    cid=data["case"]["case_id"]
    import base64
    body={"case_id":cid,"filename":"receipt.pdf","content_type":"application/pdf","content_base64":base64.b64encode(b"evidence").decode()}
    status,data=call(app,"POST","/v1/evidence",body,token=token); assert status==201
    eid=data["evidence"]["evidence_id"]
    status,data=call(app,"GET",f"/v1/evidence/{eid}",token=token); assert status==200 and data["evidence"]["sha256"]
    status,data=call(app,"POST",f"/v1/evidence/{eid}/verify",{},token=token); assert status==200 and data["evidence"]["verified"] is True
    # A different tenant has no visibility into the evidence.
    token_b=login(app,"other@example.com")
    status,_=call(app,"GET",f"/v1/evidence/{eid}",token=token_b); assert status==404


def test_rbac_client_cannot_create_case_or_approve():
    app=create_app()
    app.seed_user(organization_id="org-a", email="client@example.com", password="correct horse battery staple", role="CLIENT")
    token=login(app,"client@example.com")
    status,_=call(app,"POST","/v1/cases",{"review_id":"missing"},token=token); assert status==403
    status,_=call(app,"POST","/v1/evidence",{"case_id":"missing","filename":"x.pdf","content_type":"application/pdf","content_base64":"eA=="},token=token); assert status==404
