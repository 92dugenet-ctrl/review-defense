import pytest
from src.submission_workspace import (
    create_submission, prepare_submission, request_approval, approve_submission,
    invalidate_if_modified, mark_submitted, update_status, content_hash,
    can_edit_submission, can_approve_submission, can_record_external_submission,
)


def make(kind="INITIAL_REPORT"):
    return create_submission(
        submission_id="s1", case_id="c1", organization_id="org-a", kind=kind,
        content="The review contains a potential policy violation. Evidence is attached.",
        created_at="2026-09-20T13:00:00Z", created_by="analyst",
    )


def test_prepare_hashes_content_and_requires_content():
    s = prepare_submission(make())
    assert s.content_sha256 == content_hash(s.content)
    with pytest.raises(ValueError):
        create_submission(submission_id="s2", case_id="c1", organization_id="org-a",
                          kind="INITIAL_REPORT", content=" ", created_at="now", created_by="u")


def test_approval_requires_preparation_and_authorized_role():
    with pytest.raises(ValueError):
        request_approval(make())
    s = request_approval(prepare_submission(make()))
    with pytest.raises(PermissionError):
        approve_submission(submission=s, actor_id="client", actor_role="CLIENT",
                           approval_id="a1", approved_at="2026-09-20T13:02:00Z")
    approved, event = approve_submission(submission=s, actor_id="admin", actor_role="ADMIN",
                                          approval_id="a1", approved_at="2026-09-20T13:02:00Z")
    assert approved.status == "APPROVED"
    assert event.content_sha256 == s.content_sha256


def test_content_modification_invalidates_approval():
    s = request_approval(prepare_submission(make()))
    s, _ = approve_submission(submission=s, actor_id="admin", actor_role="ADMIN",
                              approval_id="a1", approved_at="2026-09-20T13:02:00Z")
    invalid = invalidate_if_modified(submission=s, modified_content="changed content",
                                     invalidated_at="2026-09-20T13:03:00Z")
    assert invalid.status == "INVALIDATED"
    assert invalid.approved_by is None


def test_external_submission_is_only_recorded_after_approval():
    s = request_approval(prepare_submission(make()))
    with pytest.raises(ValueError):
        mark_submitted(submission=s, submitted_at="now", external_reference="google-1")
    approved, _ = approve_submission(submission=s, actor_id="admin", actor_role="ADMIN",
                                      approval_id="a1", approved_at="now")
    submitted = mark_submitted(submission=approved, submitted_at="later", external_reference="google-1")
    assert submitted.status == "SUBMITTED"
    assert submitted.external_reference == "google-1"


def test_tracking_transitions_are_separate_from_external_action():
    s = request_approval(prepare_submission(make()))
    s, _ = approve_submission(submission=s, actor_id="admin", actor_role="ADMIN",
                              approval_id="a1", approved_at="now")
    s = mark_submitted(submission=s, submitted_at="later", external_reference="ref-1")
    s = update_status(submission=s, status="UNDER_REVIEW")
    s = update_status(submission=s, status="APPEAL_ELIGIBLE")
    assert s.status == "APPEAL_ELIGIBLE"
    with pytest.raises(ValueError):
        update_status(submission=s, status="APPROVED")


def test_appeal_is_a_distinct_submission_kind():
    appeal = prepare_submission(make("APPEAL"))
    assert appeal.kind == "APPEAL"
    assert appeal.status == "DRAFT"


def test_permissions_are_explicit():
    assert can_edit_submission("ANALYST")
    assert can_approve_submission("OWNER")
    assert can_record_external_submission("ADMIN")
    assert not can_edit_submission("CLIENT")
    assert not can_approve_submission("CLIENT")


def test_tenant_identity_is_preserved():
    s = prepare_submission(make())
    assert s.organization_id == "org-a"
    approved, event = approve_submission(submission=request_approval(s), actor_id="admin",
                                          actor_role="ADMIN", approval_id="a1", approved_at="now")
    assert event.organization_id == "org-a"
