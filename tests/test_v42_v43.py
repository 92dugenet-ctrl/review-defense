from src.operations_ui import (
    ReviewSummary, ClaimView, PolicySignalView, EvidenceView, TimelineEvent,
    Contradiction, CaseWorkspace, create_evidence_document, integrity_matches,
    missing_evidence_tasks, case_requires_human_review, role_can_edit_evidence,
    role_can_verify_evidence, fingerprint,
)


def make_case(**kwargs):
    base = dict(
        case_id="c1", organization_id="org-a", state="HUMAN_REVIEW", priority="HIGH",
        review=ReviewSummary("r1", 2, "Service lent", "2026-09-20T10:00:00Z"),
    )
    base.update(kwargs)
    return CaseWorkspace(**base)


def test_case_workspace_is_tenant_bound_and_exposes_operational_data():
    c = make_case(
        claims=(ClaimView("cl1", "Waited two hours", "EXPERIENCE", "UNVERIFIED"),),
        policies=(PolicySignalView("RD-P03", "POSSIBLE", "Affiliation needs evidence"),),
        evidence=(EvidenceView("e1", "booking.pdf", "BOOKING", "abc", "VERIFIED"),),
    )
    assert c.organization_id == "org-a"
    assert c.claims[0].claim_id == "cl1"
    assert c.policies[0].code == "RD-P03"
    assert c.evidence[0].status == "VERIFIED"


def test_contradiction_forces_human_review():
    c = make_case(contradictions=(Contradiction("x", "timestamps conflict", "cl1", ("e1", "e2")),))
    assert case_requires_human_review(c)


def test_evidence_hash_detects_modification():
    doc = create_evidence_document(
        evidence_id="e1", organization_id="org-a", filename="invoice.pdf",
        mime_type="application/pdf", content=b"original",
    )
    assert integrity_matches(doc, b"original")
    assert not integrity_matches(doc, b"modified")
    assert doc.content_sha256 == fingerprint(b"original")


def test_missing_evidence_tasks_are_explicit():
    c = make_case(evidence=(EvidenceView("e1", "booking.pdf", "BOOKING", "abc"),))
    tasks = missing_evidence_tasks(c, {"cl1": ["BOOKING", "CUSTOMER_RECORD"]})
    assert [t.evidence_requirement for t in tasks] == ["CUSTOMER_RECORD"]


def test_evidence_permissions_are_separated():
    assert role_can_edit_evidence("CLIENT")
    assert role_can_verify_evidence("ANALYST")
    assert not role_can_verify_evidence("CLIENT")
    assert not role_can_edit_evidence("VIEWER")
