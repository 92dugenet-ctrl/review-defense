import pytest
from src.outcome_workspace import (
    record_outcome, can_record_outcome, can_close_outcome,
    outcome_requires_appeal, outcome_is_final, summarize_outcomes,
)

def make(kind="REJECTED"):
    return record_outcome(
        outcome_id="o1", organization_id="org-a", submission_id="s1", case_id="c1",
        kind=kind, recorded_at="2026-09-20T14:00:00Z", recorded_by="admin",
        source="GOOGLE_UI", reason="External response recorded by analyst.",
        external_reference="ref-1")

def test_records_outcome_without_inference():
    o = make()
    assert o.kind == "REJECTED"
    assert o.reason.startswith("External")

def test_supported_outcome_kinds():
    for kind in ["REMOVED", "REJECTED", "NO_RESPONSE", "APPEAL_AVAILABLE", "APPEAL_REJECTED", "APPEALED", "CLOSED", "UNKNOWN"]:
        assert make(kind).kind == kind

def test_invalid_kind_and_blank_reason():
    with pytest.raises(ValueError):
        make("NOT_A_REAL_OUTCOME")
    with pytest.raises(ValueError):
        record_outcome(outcome_id="o", organization_id="org", submission_id="s", case_id="c",
                       kind="UNKNOWN", recorded_at="now", recorded_by="u", source="ui", reason=" ")

def test_permissions():
    assert can_record_outcome("ANALYST")
    assert can_record_outcome("ADMIN")
    assert can_close_outcome("OWNER")
    assert not can_record_outcome("CLIENT")
    assert not can_close_outcome("VIEWER")

def test_appeal_and_final_semantics_are_descriptive():
    assert outcome_requires_appeal("REJECTED")
    assert outcome_requires_appeal("APPEAL_AVAILABLE")
    assert not outcome_requires_appeal("REMOVED")
    assert outcome_is_final("REMOVED")
    assert outcome_is_final("CLOSED")
    assert not outcome_is_final("APPEALED")

def test_summary_is_descriptive():
    values = (make("REJECTED"), make("APPEAL_AVAILABLE"), make("REJECTED"))
    assert summarize_outcomes(values) == {"REJECTED": 2, "APPEAL_AVAILABLE": 1}

def test_tenant_identity_is_preserved():
    o = make()
    assert o.organization_id == "org-a"
    assert o.case_id == "c1"
    assert o.submission_id == "s1"

def test_external_reference_is_optional():
    o = record_outcome(outcome_id="o2", organization_id="org-a", submission_id="s2", case_id="c2",
                       kind="NO_RESPONSE", recorded_at="now", recorded_by="admin", source="MANUAL")
    assert o.external_reference is None
