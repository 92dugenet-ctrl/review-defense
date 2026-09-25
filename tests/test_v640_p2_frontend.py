from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_navigation_has_recoverable_editorial_failure_path():
    text = (ROOT / "frontend/assets/public.js").read_text()
    assert "__seoArticlesPromise=null" in text
    assert "__seoArticlesPromise=null;finish(()=>reject" in text
    assert "function publicLoadError()" in text
    assert "bootPublicRoute()" in text
    assert "public-error-state" in text


def test_public_recovery_state_is_responsive():
    text = (ROOT / "frontend/assets/public.css").read_text()
    assert ".public-error-state" in text
    assert ".public-error-card" in text
    assert ".public-retry" in text
    assert "@media(max-width:620px)" in text


def test_public_asset_version_is_consistent_after_p2():
    js = (ROOT / "frontend/assets/public.js").read_text()
    index = (ROOT / "frontend/index.html").read_text()
    landing = (ROOT / "frontend/landing.html").read_text()
    assert "PUBLIC_ASSET_VERSION='6710'" in js
    assert "public.js?v=6710" in index
    assert "public.js?v=6710" in landing
