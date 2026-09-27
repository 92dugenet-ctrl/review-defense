import pytest
from src.api_server import MemoryStore
from src.notification_service import NotificationService
from src.notification_policy import NotificationPolicy
from src.notification_delivery import DeliveryError

class Repo:
    def __init__(self): self.created=[]; self.updated=[]; self.attempts=[]
    def create_notification(self,o,p): self.created.append(p)
    def update_notification(self,o,p): self.updated.append(p)
    def record_notification_attempt(self,o,p): self.attempts.append(p)

def make(delivery=None):
    store=MemoryStore(); repo=Repo()
    svc=NotificationService(store=store,repository=repo,audit_event=store.audit_event,delivery_func=delivery,
        policy_provider=lambda _: NotificationPolicy("org-a"))
    return store,repo,svc

def queue(svc):
    return svc.queue(organization_id="org-a",case_id="c1",level="DUE",channel="IN_APP",target="u1",
        subject="Alert",body="Body",actor_id="admin")

def test_queue_deduplicates_and_persists():
    store,repo,svc=make(); first,d1=queue(svc); second,d2=queue(svc)
    assert not d1 and d2 and first.notification_id==second.notification_id
    assert len(repo.created)==1 and len(store.notifications)==1

def test_cancel_and_mark_sent_enforce_pending():
    store,repo,svc=make(); n,_=queue(svc)
    assert svc.cancel(organization_id="org-a",notification_id=n.notification_id,actor_id="admin").status=="CANCELLED"
    with pytest.raises(ValueError): svc.mark_sent(organization_id="org-a",notification_id=n.notification_id,actor_id="admin")

def test_delivery_failure_records_attempt():
    def fail(notification,*,email_config): raise DeliveryError("transport failed")
    store,repo,svc=make(fail); n,_=queue(svc)
    with pytest.raises(DeliveryError): svc.deliver(organization_id="org-a",notification_id=n.notification_id,actor_id="admin")
    assert n.delivery_attempts==1 and n.delivery_error=="transport failed" and len(repo.attempts)==1

def test_delivery_success_marks_sent():
    def ok(notification,*,email_config): return type("Result",(),{"provider":"test"})()
    store,repo,svc=make(ok); n,_=queue(svc)
    sent,result=svc.deliver(organization_id="org-a",notification_id=n.notification_id,actor_id="admin")
    assert sent.status=="SENT" and result.provider=="test"

def test_policy_blocks_queue():
    store,repo,svc=make()
    svc.policy_provider=lambda _: NotificationPolicy("org-a",enabled=False)
    with pytest.raises(PermissionError): queue(svc)


def test_policy_list_metrics_and_worker_are_service_owned():
    from types import SimpleNamespace
    store, repo, svc = make(lambda notification, *, email_config: SimpleNamespace(provider="test"))
    policy, configured = svc.policy_for_organization(organization_id="org-a")
    assert configured is False and policy.payload()["levels"] == ["DUE", "CRITICAL"]
    updated = svc.set_policy(organization_id="org-a", payload={"levels": ["CRITICAL"]}, actor_id="admin")
    assert updated.payload()["levels"] == ["CRITICAL"]
    n, _ = queue(svc)
    assert svc.list_for_organization(organization_id="org-a")[0]["notification_id"] == n.notification_id
    assert svc.metrics_for_organization(organization_id="org-a")["notifications"]["total"] == 1
    result = svc.run_worker(organization_id="org-a", limit=1, actor_id="admin")
    assert result.sent == 1
