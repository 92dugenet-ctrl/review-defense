from types import SimpleNamespace
from src.notification_observability import build_notification_metrics
from src.notification_outbox import create_notification


def make(org="org-a", channel="EMAIL", level="DUE"):
    return create_notification(organization_id=org, case_id="case-1", level=level, channel=channel, target="ops", subject="Alert", body="Review", actor_id="u1")


def test_metrics_are_tenant_scoped_and_aggregate_delivery_state():
    a=make(); a.status="SENT"; a.delivery_attempts=2
    b=make(channel="WEBHOOK", level="CRITICAL"); b.delivery_attempts=1; b.dead_lettered_at="2026-01-01T00:00:00+00:00"
    other=make("org-b")
    audit=[
        {"organization_id":"org-a","action":"ESCALATION_NOTIFICATION_QUEUED"},
        {"organization_id":"org-a","action":"ESCALATION_NOTIFICATION_DELIVERED"},
        {"organization_id":"org-a","action":"ESCALATION_NOTIFICATION_DELIVERY_FAILED"},
        {"organization_id":"org-a","action":"ESCALATION_NOTIFICATION_RETRY_SCHEDULED"},
        {"organization_id":"org-a","action":"NOTIFICATION_WORKER_RUN"},
        {"organization_id":"org-b","action":"ESCALATION_NOTIFICATION_DELIVERED"},
    ]
    m=build_notification_metrics([a,b,other],audit,organization_id="org-a")
    assert m["notifications"]["total"]==2
    assert m["notifications"]["by_channel"]=={"EMAIL":1,"WEBHOOK":1}
    assert m["notifications"]["by_level"]=={"CRITICAL":1,"DUE":1}
    assert m["delivery"]["attempts"]==3 and m["delivery"]["dead_lettered"]==1
    assert m["delivery"]["delivered_events"]==1 and m["delivery"]["failed_events"]==1 and m["delivery"]["retry_events"]==1
    assert m["workflow"]["worker_runs"]==1


def test_metrics_require_tenant():
    import pytest
    with pytest.raises(ValueError): build_notification_metrics([], [], organization_id="")


def test_api_metrics_endpoint_is_tenant_scoped():
    import io,json
    from src.api_server import ReviewDefenseAPI
    app=ReviewDefenseAPI()
    app.seed_user(organization_id="org-a",email="a@example.com",password="StrongPass123!",role="ANALYST")
    app.seed_user(organization_id="org-b",email="b@example.com",password="StrongPass123!",role="ANALYST")
    def call(method,path,body=None,token=None):
        raw=json.dumps(body or {}).encode(); env={"REQUEST_METHOD":method,"PATH_INFO":path,"REMOTE_ADDR":"127.0.0.1","CONTENT_LENGTH":str(len(raw)),"wsgi.input":io.BytesIO(raw)}
        if token: env["HTTP_AUTHORIZATION"]="Bearer "+token
        out={}; data=b"".join(app(env,lambda status,headers: out.update(status=status,headers=headers))); return out["status"],json.loads(data)
    _,login=call("POST","/v1/auth/login",{"email":"a@example.com","password":"StrongPass123!"}); token=login["access_token"]
    n=make("org-a"); app.store.notifications[("org-a",n.notification_id)]=n
    status,payload=call("GET","/v1/notifications/metrics",token=token)
    assert status=="200 OK" and payload["metrics"]["organization_id"]=="org-a" and payload["metrics"]["notifications"]["total"]==1


def test_metrics_read_only_does_not_mutate_notification():
    n=make(); before=n.payload(); build_notification_metrics([n],[],organization_id="org-a"); assert n.payload()==before
