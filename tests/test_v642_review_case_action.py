from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_review_inbox_exposes_case_creation_action():
    js = (ROOT / "frontend/assets/app.js").read_text(encoding="utf-8")
    assert "createCaseFromReview" in js
    assert "api('/v1/cases'" in js
    assert "review_id:reviewId" in js
    assert "Idempotency-Key" in js
    assert "Créer le dossier" in js


def test_review_to_case_action_has_mobile_layout():
    css = (ROOT / "frontend/assets/app.css").read_text(encoding="utf-8")
    assert ".review-card-actions" in css
    assert ".primary.compact" in css
    assert "@media(max-width:600px)" in css
