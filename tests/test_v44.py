from src.app_shell import ROUTES, SessionContext, can_access
from src.review_workspace import (
    ReviewContext, ReviewHistory, ReviewChange, build_review_workspace,
    can_modify_review_analysis, can_submit_from_review_workspace,
    review_belongs_to_organization,
)


def make_review(text="J'ai attendu 2 heures, c'était inadmissible."):
    return ReviewContext(
        review_id="r1", organization_id="org-a", location_id="loc-1",
        author_display_name="Client", rating=2, text=text,
        published_at="2026-09-20T10:00:00Z", source="GOOGLE",
    )


def test_review_workspace_extracts_claims_and_keeps_opinion_separate():
    ws = build_review_workspace(make_review())
    assert [c.claim_type for c in ws.claims] == ["EXPERIENCE", "OPINION"]
    assert ws.human_review_required is False


def test_material_allegation_creates_candidate_signal_and_human_review():
    ws = build_review_workspace(make_review("Le serveur m'a volé 200€."))
    assert ws.claims[0].claim_type == "ALLEGATION"
    assert ws.policy_signals[0].code == "RD-P04"
    assert ws.policy_signals[0].status == "POSSIBLE"
    assert ws.human_review_required


def test_review_history_is_attached_to_same_review():
    history = ReviewHistory(
        "r1", "2026-09-01T00:00:00Z", "2026-09-20T10:00:00Z",
        (ReviewChange("ch1", "r1", "2026-09-20T10:00:00Z", "text", "old", "new", "GOOGLE"),),
    )
    ws = build_review_workspace(make_review(), history=history, case_id="c1")
    assert ws.case_id == "c1"
    assert ws.history.changes[0].field == "text"


def test_tenant_isolation_and_roles():
    review = make_review()
    assert review_belongs_to_organization(review, "org-a")
    assert not review_belongs_to_organization(review, "org-b")
    assert can_modify_review_analysis("ANALYST")
    assert not can_modify_review_analysis("CLIENT")
    assert not can_submit_from_review_workspace("OWNER")


def test_review_detail_route_is_available_but_no_external_action_is_exposed():
    assert ROUTES["/reviews/:id"] == "review_intelligence_workspace"
    assert can_access(SessionContext("u1", "org-a", "CLIENT"), "/reviews/:id")
    assert can_access(SessionContext("u2", "org-a", "ANALYST"), "/reviews/:id")
