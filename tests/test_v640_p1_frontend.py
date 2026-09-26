from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_shell_does_not_eagerly_load_seo_editorial_payload():
    for name in ("frontend/index.html", "frontend/landing.html"):
        text = (ROOT / name).read_text()
        assert "seo-articles.js" not in text
        assert "public.js?v=6711" in text


def test_public_js_has_deferred_seo_loader_and_single_history_listener():
    text = (ROOT / "frontend/assets/public.js").read_text()
    assert "function ensureSeoArticles()" in text
    assert "script.async=true" in text
    assert "function bootPublicRoute()" in text
    assert text.count("window.addEventListener('popstate'") == 1
    assert "publicLoadingState()" in text
    assert "clearPublicLoading()" in text


def test_public_css_has_navigation_loading_fallback():
    text = (ROOT / "frontend/assets/public.css").read_text()
    assert ".public-loading" in text
    assert ".marketing.is-navigating" in text
    assert "prefers-reduced-motion:reduce" in text
