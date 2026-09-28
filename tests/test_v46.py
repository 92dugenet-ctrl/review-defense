import pytest
from src.decision_workspace import (
    freeze_dossier, dossier_hash, snapshot_matches, create_decision,
    attach_snapshot, request_approval, approve_decision, invalidate_if_modified,
    can_create_decision, can_request_approval, can_approve_decision,
    can_submit_after_approval,
)


def make_decision():
    return create_decision(
        decision_id="d1", case_id="c1", organization_id="org-a",
        kind="PREPARE_REPORT", rationale="Potential policy violation with evidence to review.",
        created_at="2026-09-20T12:00:00Z", created_by="u-analyst",
    )


def test_snapshot_is_canonical_and_tenant_bound():
    payload = {"claims": [{"id": "cl1", "status": "SUPPORTED"}], "policies": ["RD-P08"]}
    snap = freeze_dossier(case_id="c1", organization_id="org-a", payload=payload,
                          frozen_at="2026-09-20T12:01:00Z", frozen_by="u1")
    assert snap.sha256 == dossier_hash(payload)
    assert snapshot_matches(snap, {"policies": ["RD-P08"], "claims": [{"status": "SUPPORTED", "id": "cl1"}]})
    assert snap.organization_id == "org-a"


def test_decision_must_be_frozen_before_approval():
    with pytest.raises(ValueError):
        request_approval(make_decision())
    d = attach_snapshot(make_decision(), freeze_dossier(
        case_id="c1", organization_id="org-a", payload={"x": 1},
        frozen_at="2026-09-20T12:01:00Z", frozen_by="u1"))
    assert d.status == "FROZEN"
    assert request_approval(d).status == "PENDING_APPROVAL"


def test_approval_requires_authorized_role_and_exact_snapshot():
    snap = freeze_dossier(case_id="c1", organization_id="org-a", payload={"x": 1},
                          frozen_at="2026-09-20T12:01:00Z", frozen_by="u1")
    d = request_approval(attach_snapshot(make_decision(), snap))
    with pytest.raises(PermissionError):
        approve_decision(decision=d, snapshot=snap, actor_id="client", actor_role="CLIENT",
                         approval_id="a1", approved_at="2026-09-20T12:02:00Z")
    approved, event = approve_decision(decision=d, snapshot=snap, actor_id="admin", actor_role="ADMIN",
                                       approval_id="a1", approved_at="2026-09-20T12:02:00Z")
    assert approved.status == "APPROVED"
    assert event.snapshot_sha256 == snap.sha256


def test_modified_dossier_invalidates_pending_or_approved_decision():
    snap = freeze_dossier(case_id="c1", organization_id="org-a", payload={"x": 1},
                          frozen_at="2026-09-20T12:01:00Z", frozen_by="u1")
    d = request_approval(attach_snapshot(make_decision(), snap))
    invalid = invalidate_if_modified(decision=d, snapshot=snap, current_payload={"x": 2},
                                     invalidated_at="2026-09-20T12:03:00Z")
    assert invalid.status == "INVALIDATED"
    assert invalid.invalidation_reason == "dossier_modified"


def test_tenant_mismatch_is_blocked():
    d = make_decision()
    other = freeze_dossier(case_id="c1", organization_id="org-b", payload={},
                           frozen_at="2026-09-20T12:01:00Z", frozen_by="u1")
    with pytest.raises(ValueError):
        attach_snapshot(d, other)


def test_permissions_and_no_external_submission_side_effect():
    assert can_create_decision("ANALYST")
    assert can_request_approval("ADMIN")
    assert can_approve_decision("OWNER")
    assert not can_approve_decision("CLIENT")
    d = attach_snapshot(make_decision(), freeze_dossier(case_id="c1", organization_id="org-a", payload={},
                                                        frozen_at="2026-09-20T12:01:00Z", frozen_by="u1"))
    assert not can_submit_after_approval("ADMIN", d)
    approved, _ = approve_decision(decision=request_approval(d), snapshot=freeze_dossier(
        case_id="c1", organization_id="org-a", payload={}, frozen_at="2026-09-20T12:01:00Z", frozen_by="u1"),
        actor_id="admin", actor_role="ADMIN", approval_id="a1", approved_at="2026-09-20T12:02:00Z")
    assert can_submit_after_approval("ADMIN", approved)
