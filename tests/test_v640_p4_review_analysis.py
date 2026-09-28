import io, json, base64
from wsgiref.util import setup_testing_defaults

from src.api_server import create_app


def call(app, method, path, body=None, token=None):
    raw = json.dumps(body or {}).encode()
    env = {}
    setup_testing_defaults(env)
    env.update({"REQUEST_METHOD": method, "PATH_INFO": path, "wsgi.input": io.BytesIO(raw), "CONTENT_LENGTH": str(len(raw)), "REMOTE_ADDR": "test"})
    if token:
        env["HTTP_AUTHORIZATION"] = "Bearer " + token
    out = {}
    def sr(status, headers):
        out["status"] = int(status.split()[0])
    data = b"".join(app(env, sr))
    return out["status"], json.loads(data)


def login(app, email):
    status, data = call(app, "POST", "/v1/auth/login", {"email": email, "password": "correct horse battery staple"})
    assert status == 200
    return data["access_token"]


def test_p4_review_analysis_and_evidence_status_contract():
    app = create_app()
    app.seed_user(organization_id="p4-org", email="owner@example.com", password="correct horse battery staple", role="OWNER")
    token = login(app, "owner@example.com")
    status, _ = call(app, "POST", "/v1/reviews", {"review_id": "review-p4", "rating": 1, "text": "Le produit est cassé et le support ne répond pas.", "author_display_name": "Test User"}, token)
    assert status == 201
    status, data = call(app, "GET", "/v1/reviews/review-p4", token=token)
    assert status == 200 and data["claims"] and "policy_signals" in data
    status, data = call(app, "POST", "/v1/cases", {"review_id": "review-p4"}, token)
    assert status == 201
    case_id = data["case"]["case_id"]
    status, data = call(app, "POST", "/v1/evidence", {"case_id": case_id, "filename": "support.txt", "content_type": "text/plain", "content_base64": base64.b64encode(b"Support ticket #42").decode(), "facts": [{"key": "ticket", "kind": "reference", "value": "42"}]}, token)
    assert status == 201
    evidence_id = data["evidence"]["evidence_id"]
    assert data["evidence"]["status"] == "PENDING"
    status, data = call(app, "GET", "/v1/evidence", token=token)
    assert status == 200
    evidence = next(x for x in data["items"] if x["evidence_id"] == evidence_id)
    assert evidence["status"] == "PENDING"
    status, data = call(app, "POST", f"/v1/evidence/{evidence_id}/verify", token=token)
    assert status == 200 and data["evidence"]["status"] == "VERIFIED"
    status, data = call(app, "GET", "/v1/evidence", token=token)
    assert status == 200
    evidence = next(x for x in data["items"] if x["evidence_id"] == evidence_id)
    assert evidence["status"] == "VERIFIED"
