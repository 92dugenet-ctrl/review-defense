import base64
from datetime import datetime, timedelta, timezone
import pytest

from src.e2e_pipeline import ReviewDefenseE2E
from src.evidence_vault import sign_download_url, verify_download_url
from src.review_workspace import ReviewContext
from src.security_hardening import Session, generate_session_token


def review(org="org-a", review_id="r1", text="Payez 500 € et je supprime mes avis."):
    return ReviewContext(review_id, org, "loc-1", "Alice", 1, text,
                         "2026-09-20T10:00:00Z")


def test_full_pipeline_reaches_approved_submission_boundary():
    app = ReviewDefenseE2E()
    ws = app.ingest(review())
    assert ws.human_review_required
    stored = app.add_evidence(evidence_id="e1", review_id="r1", content=b"request 500 EUR", filename="message.pdf")
    assert stored.sha256
    decision, approval = app.freeze_and_approve_decision(
        decision_id="d1", case_id="c1", payload={"review_id": "r1", "policy": "RD-P10", "evidence": ["e1"]}
    )
    assert decision.status == "APPROVED"
    assert approval.snapshot_sha256 == decision.snapshot_sha256
    submission, _ = app.prepare_and_approve_submission(
        submission_id="s1", case_id="c1", content="Documented report: potential extortion signal; evidence attached."
    )
    assert submission.status == "APPROVED"
    assert not app.gateway.is_configured()
    assert app.external_calls == 0


def test_review_ingestion_is_idempotency_guarded():
    app = ReviewDefenseE2E()
    app.ingest(review())
    with pytest.raises(ValueError, match="duplicate"):
        app.ingest(review())


def test_cross_tenant_review_rejected():
    app = ReviewDefenseE2E(organization_id="org-a")
    with pytest.raises(PermissionError):
        app.ingest(review(org="org-b"))


def test_malformed_review_rejected():
    app = ReviewDefenseE2E()
    with pytest.raises(ValueError):
        app.ingest(ReviewContext("r1", "org-a", "loc", None, 6, "text", "now"))
    with pytest.raises(ValueError):
        app.ingest(ReviewContext("r2", "org-a", "loc", None, 1, " ", "now"))


def test_legitimate_negative_opinion_produces_no_policy_signal():
    app = ReviewDefenseE2E()
    ws = app.ingest(review(text="Service très lent, 1h d'attente. Je n'ai pas aimé."))
    assert ws.policy_signals == ()
    assert not ws.human_review_required


def test_allegation_requires_evidence_and_human_review():
    app = ReviewDefenseE2E()
    ws = app.ingest(review(text="Ils m'ont volé 100 € et c'est inadmissible."))
    assert any(p.code == "RD-P04" for p in ws.policy_signals)
    assert ws.human_review_required


def test_missing_evidence_is_not_treated_as_proof_of_falsity():
    app = ReviewDefenseE2E()
    ws = app.ingest(review(text="Ils m'ont volé 100 €."))
    assert ws.claims[0].status == "UNVERIFIED"


def test_evidence_vault_tenant_isolation_in_e2e_flow():
    app = ReviewDefenseE2E()
    app.ingest(review())
    obj = app.add_evidence(evidence_id="e1", review_id="r1", content=b"x", filename="x.pdf")
    with pytest.raises(PermissionError):
        app.evidence_store.get(organization_id="org-b", object_key=obj.object_key)


def test_invalid_upload_fails_inside_e2e_flow():
    app = ReviewDefenseE2E()
    app.ingest(review())
    with pytest.raises(ValueError, match="unsupported"):
        app.add_evidence(evidence_id="e1", review_id="r1", content=b"x", filename="x.exe", content_type="application/octet-stream")


def test_corrupted_evidence_detected():
    app = ReviewDefenseE2E()
    app.ingest(review())
    obj = app.add_evidence(evidence_id="e1", review_id="r1", content=b"original", filename="x.pdf")
    assert not __import__("src.evidence_vault", fromlist=["verify_integrity"]).verify_integrity(b"tampered", obj.sha256)


def test_dossier_modification_invalidates_approval():
    app = ReviewDefenseE2E()
    app.ingest(review())
    decision, _ = app.freeze_and_approve_decision(decision_id="d1", case_id="c1", payload={"x": 1})
    assert decision.status == "APPROVED"
    updated = app.invalidate_modified_dossier(decision_id="d1", payload={"x": 2})
    assert updated.status == "INVALIDATED"


def test_unchanged_dossier_keeps_approval_valid():
    app = ReviewDefenseE2E()
    app.ingest(review())
    decision, _ = app.freeze_and_approve_decision(decision_id="d1", case_id="c1", payload={"x": 1})
    updated = app.invalidate_modified_dossier(decision_id="d1", payload={"x": 1})
    assert updated.status == "APPROVED"


def test_client_cannot_approve_decision():
    app = ReviewDefenseE2E()
    app.ingest(review())
    from src.decision_workspace import create_decision, freeze_dossier, attach_snapshot, request_approval, approve_decision
    d = create_decision(decision_id="d1", case_id="c1", organization_id="org-a", kind="HUMAN_REVIEW", rationale="review", created_at="now", created_by="analyst")
    s = freeze_dossier(case_id="c1", organization_id="org-a", payload={"x": 1}, frozen_at="now", frozen_by="analyst")
    d = request_approval(attach_snapshot(d, s))
    with pytest.raises(PermissionError):
        approve_decision(decision=d, snapshot=s, actor_id="client", actor_role="CLIENT", approval_id="a", approved_at="now")


def test_submission_cannot_be_marked_submitted_before_approval():
    app = ReviewDefenseE2E()
    app.ingest(review())
    from src.submission_workspace import create_submission, mark_submitted
    s = create_submission(submission_id="s", case_id="c", organization_id="org-a", kind="INITIAL_REPORT", content="report", created_at="now", created_by="a")
    with pytest.raises(ValueError):
        mark_submitted(submission=s, submitted_at="now", external_reference="manual-1")


def test_external_submission_is_explicit_record_only():
    app = ReviewDefenseE2E()
    app.ingest(review())
    app.prepare_and_approve_submission(submission_id="s1", case_id="c1", content="report")
    s = app.record_external_submission(submission_id="s1", external_reference="google-case-123")
    assert s.status == "SUBMITTED"
    assert app.external_calls == 0


def test_outcome_is_observed_not_inferred():
    app = ReviewDefenseE2E()
    app.ingest(review())
    app.prepare_and_approve_submission(submission_id="s1", case_id="c1", content="report")
    app.record_external_submission(submission_id="s1", external_reference="google-case-123")
    outcome = app.record_outcome(outcome_id="o1", submission_id="s1", case_id="c1", kind="REJECTED", source="MANUAL")
    assert outcome.kind == "REJECTED"
    assert outcome.reason is None


def test_signed_download_is_tenant_bound_and_expires():
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    key = "evidence/org-a/e1/object.pdf"
    url = sign_download_url(object_key=key, organization_id="org-a", secret=b"secret", expires_in=60, now=now)
    query = dict(item.split("=", 1) for item in url.split("?", 1)[1].split("&"))
    key2 = __import__("base64").urlsafe_b64decode(query["key"] + "==").decode()
    exp = int(query["exp"])
    assert verify_download_url(object_key=key2, organization_id="org-a", expires_at=exp, signature=query["sig"], secret=b"secret", now=now)
    assert not verify_download_url(object_key=key2, organization_id="org-b", expires_at=exp, signature=query["sig"], secret=b"secret", now=now)
    assert not verify_download_url(object_key=key2, organization_id="org-a", expires_at=exp, signature=query["sig"], secret=b"secret", now=now + timedelta(seconds=61))


def test_session_tenant_boundary_is_enforced():
    app = ReviewDefenseE2E()
    raw, session = app.new_session()
    assert session.matches(raw)
    app.authorize(session, "org-a")
    with pytest.raises(PermissionError):
        app.authorize(session, "org-b")


def test_expired_session_rejected():
    raw, token_hash = generate_session_token()
    session = Session("u", "org-a", "ANALYST", token_hash, datetime.now(timezone.utc) - timedelta(seconds=1))
    app = ReviewDefenseE2E()
    with pytest.raises(PermissionError):
        app.authorize(session, "org-a")
    assert not session.matches(raw)


def test_snapshot_is_immutable_copy_and_hash_stable():
    app = ReviewDefenseE2E()
    app.ingest(review())
    payload = {"nested": {"x": 1}}
    decision, _ = app.freeze_and_approve_decision(decision_id="d", case_id="c", payload=payload)
    payload["nested"]["x"] = 99
    assert decision.snapshot_sha256 == app.snapshots["d"].sha256
    assert app.snapshots["d"].payload["nested"]["x"] == 1


def test_case_builder_carries_policy_signals_into_human_review_state():
    app = ReviewDefenseE2E()
    app.ingest(review(text="Payez 500 € et je supprime mes avis."))
    case = app.build_case(case_id="c1", review_id="r1")
    assert case.state == "HUMAN_REVIEW"
    assert any(p.code == "RD-P10" for p in case.policies)
