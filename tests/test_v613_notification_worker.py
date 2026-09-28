from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from src.notification_outbox import create_notification
from src.notification_worker import NotificationWorker, backoff_seconds


def n(org="org-a", channel="IN_APP"):
    return create_notification(organization_id=org, case_id="case-1", level="DUE", channel=channel, target="ops", subject="Alert", body="Review", actor_id="u1")


def test_worker_sends_due_notification_and_persists_and_audits():
    clock=lambda: datetime(2026,1,1,tzinfo=timezone.utc)
    sent=[]; audited=[]
    w=NotificationWorker(delivery_func=lambda notification, email_config: SimpleNamespace(provider="test"), clock=clock)
    item=n(); w.run_once([item], organization_id="org-a", actor_id="worker", persist=lambda x: sent.append(x.status), audit=lambda *a,**k: audited.append((a,k)))
    assert item.status == "SENT" and sent == ["SENT"]
    assert any(x[1].get("worker") for x in audited)


def test_worker_retries_with_bounded_backoff_then_dead_letters():
    clock=lambda: datetime(2026,1,1,tzinfo=timezone.utc)
    w=NotificationWorker(delivery_func=lambda *a,**k: (_ for _ in ()).throw(RuntimeError("down")), clock=clock)
    item=n(); item.max_attempts=2
    r1=w.run_once([item], organization_id="org-a")
    assert r1.retried == 1 and item.status == "PENDING" and item.next_attempt_at
    item.next_attempt_at=None
    r2=w.run_once([item], organization_id="org-a")
    assert r2.dead_lettered == 1 and item.dead_lettered_at and item.status == "PENDING"


def test_worker_does_not_cross_tenant_and_skips_future_retry():
    clock=lambda: datetime(2026,1,1,tzinfo=timezone.utc)
    w=NotificationWorker(delivery_func=lambda *a,**k: (_ for _ in ()).throw(RuntimeError("must not run")), clock=clock)
    other=n("org-b"); mine=n("org-a"); mine.next_attempt_at="2026-01-02T00:00:00+00:00"
    r=w.run_once([other,mine], organization_id="org-a")
    assert r.processed == 0 and r.skipped == 1 and other.status == "PENDING"


def test_backoff_is_bounded():
    assert backoff_seconds(1) == 60
    assert backoff_seconds(2) == 300
    assert backoff_seconds(10) == 3600


def test_api_worker_requires_owner_or_admin_and_is_tenant_scoped():
    import io, json
    from src.api_server import ReviewDefenseAPI
    from src.escalation_workflow import Escalation
    app=ReviewDefenseAPI(delivery_func=lambda notification, email_config: SimpleNamespace(provider="test"))
    app.seed_user(organization_id="org-a",email="owner@example.com",password="StrongPass123!",role="OWNER")
    app.seed_user(organization_id="org-b",email="ownerb@example.com",password="StrongPass123!",role="OWNER")
    def call(method,path,body=None,token=None):
        raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
        if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
        out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)
    _,login=call("POST","/v1/auth/login",{"email":"owner@example.com","password":"StrongPass123!"}); t=login["access_token"]
    call("POST","/v1/reviews",{"review_id":"r1","text":"bad","rating":1,"published_at":"x"},t)
    _,case=call("POST","/v1/cases",{"review_id":"r1"},t); cid=case["case"]["case_id"]
    app.store.escalations[("org-a",cid,"DUE")]=Escalation(cid,"DUE","SLA breached")
    call("POST",f"/v1/escalations/{cid}/notify",{"channel":"IN_APP","target":"owner"},t)
    s,res=call("POST","/v1/notifications/worker/run",{"limit":1},t)
    assert s=="200 OK" and res["result"]["sent"]==1
