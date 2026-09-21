import json
import tempfile
from pathlib import Path

import pytest

from src.background_jobs import SQLiteJobQueue, JobState
from src.google_business_profile import GoogleBusinessProfileClient, ReviewCache
from src.google_sync_engine import ReviewEventParser, SyncStateStore, GoogleSyncEngine, SyncEventType


class FakeTransport:
    def __init__(self): self.calls=[]; self.responses=[]
    def queue(self, status, body): self.responses.append((status, {"content-type":"application/json"}, json.dumps(body).encode()))
    def request(self, method, url, **kwargs):
        self.calls.append((method,url,kwargs))
        if not self.responses: raise AssertionError("unexpected network call")
        return self.responses.pop(0)


def review(rid="r1", text="hello"):
    return {"name":f"accounts/a/locations/l/reviews/{rid}","reviewId":rid,"reviewer":{"displayName":"J"},"starRating":"FOUR","comment":text,"createTime":"2026-09-20T10:00:00Z"}


def make_engine(fake, path=":memory:"):
    def factory(org): return GoogleBusinessProfileClient(organization_id=org, access_token="tok", transport=fake)
    return GoogleSyncEngine(client_factory=factory, state=SyncStateStore(path), review_cache=ReviewCache(), queue=SQLiteJobQueue(":memory:"))


def test_pubsub_parser_accepts_new_and_updated_review_resources():
    p={"message":{"messageId":"m1","attributes":{"eventType":"NEW_REVIEW","resource":"accounts/a/locations/l/reviews/r1"}}}
    e=ReviewEventParser.parse(p)
    assert e.event_id=="m1" and e.event_type is SyncEventType.NEW_REVIEW and e.review_id=="r1"


def test_pubsub_parser_rejects_unsupported_or_malformed_events():
    with pytest.raises(ValueError): ReviewEventParser.parse({"message":{"messageId":"m1","attributes":{"eventType":"GOOGLE_UPDATE","resource":"accounts/a/locations/l"}}})
    with pytest.raises(ValueError): ReviewEventParser.parse({"message":{"messageId":"m1","attributes":{"eventType":"NEW_REVIEW","resource":"accounts/a/bad"}}})


def test_event_is_idempotent_and_fetches_specific_review():
    fake=FakeTransport(); fake.queue(200, review())
    engine=make_engine(fake)
    event=ReviewEventParser.parse({"message":{"messageId":"m1","attributes":{"eventType":"NEW_REVIEW","resource":"accounts/a/locations/l/reviews/r1"}}})
    assert engine.enqueue_event("org-a", event) is not None
    assert engine.enqueue_event("org-a", event) is None
    worker=engine.worker("org-a")
    job=worker.run_once(); assert job.state is JobState.SUCCEEDED
    assert len(engine.results("org-a","r1"))==1
    assert len(fake.calls)==1


def test_event_for_missing_review_id_reconciles_location():
    fake=FakeTransport(); fake.queue(200, {"reviews":[review("r1")],"nextPageToken":"p2"})
    engine=make_engine(fake)
    event=ReviewEventParser.parse({"message":{"messageId":"m2","attributes":{"eventType":"NEW_REVIEW","resource":"accounts/a/locations/l"}}})
    engine.enqueue_event("org-a", event)
    job=engine.worker("org-a").run_once(); assert job.state is JobState.SUCCEEDED
    assert engine.state.get_cursor("org-a","a","l").next_page_token=="p2"
    assert engine.results("org-a","r1")[0].change=="NEW"


def test_reconciliation_cursor_persists_and_resets_after_last_page():
    fake=FakeTransport()
    fake.queue(200, {"reviews":[review("r1")],"nextPageToken":"p2"})
    fake.queue(200, {"reviews":[review("r2")],"nextPageToken":None})
    engine=make_engine(fake)
    engine.enqueue_reconciliation("org-a","a","l")
    w=engine.worker("org-a")
    assert w.run_once().state is JobState.SUCCEEDED
    # enqueue a distinct reconciliation after the first job completes
    engine.enqueue_reconciliation("org-a","a","l")
    assert w.run_once().state is JobState.SUCCEEDED
    assert engine.state.get_cursor("org-a","a","l").next_page_token is None
    assert {x.review.review_id for x in engine.results("org-a")}=={"r1","r2"}
    assert "pageToken=p2" in fake.calls[1][1]


def test_reconciliation_is_tenant_isolated():
    fake=FakeTransport(); fake.queue(200,{"reviews":[review("r1")]})
    engine=make_engine(fake)
    engine.enqueue_reconciliation("org-a","a","l")
    engine.worker("org-a").run_once()
    assert engine.results("org-b")==[]
    assert engine.state.get_cursor("org-b","a","l") is None


def test_persistence_survives_reopen():
    with tempfile.TemporaryDirectory() as d:
        path=str(Path(d)/"sync.db")
        s=SyncStateStore(path); s.put_cursor("org","a","l","p2"); assert s.claim_event("org","e1"); s.close()
        s2=SyncStateStore(path)
        assert s2.get_cursor("org","a","l").next_page_token=="p2"
        assert not s2.claim_event("org","e1")
        s2.close()


def test_event_failure_is_retried_by_job_queue():
    fake=FakeTransport()  # no response: handler will fail
    engine=make_engine(fake)
    event=ReviewEventParser.parse({"message":{"messageId":"m3","attributes":{"eventType":"UPDATED_REVIEW","resource":"accounts/a/locations/l/reviews/r1"}}})
    engine.enqueue_event("org","m3" if False else event)
    w=engine.worker("org")
    job=w.run_once(); assert job.state is JobState.RETRY_SCHEDULED
    assert job.attempts==1
