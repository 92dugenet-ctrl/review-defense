from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_shell_does_not_eagerly_load_seo_editorial_payload():
    for name in ("frontend/index.html", "frontend/landing.html"):
        text = (ROOT / name).read_text()
        assert "seo-articles.js" not in text
        assert "public.js?v=6716" in text


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


def test_public_boot_is_not_short_circuited_by_console_boot_guard():
    text = (ROOT / "frontend/assets/app.js").read_text()
    assert "const __RD_PUBLIC_ROUTE=" not in text
    assert "const publicPage=typeof publicPathPage" not in text
    assert "Object.values(PUBLIC_ROUTES)" not in text
    assert "showPublicPage(publicPage||'home',false)" not in text


def test_public_scene_enrichment_runs_before_optional_visual_interactions():
    text = (ROOT / "frontend/assets/public.js").read_text()
    marker = "document.body.innerHTML=publicShell(active,body);"
    start = text.index(marker)
    end = text.index("\n}", start)
    block = text[start:end]
    assert block.index("editorializePublicPage(active);") < block.index("initPremiumInteractions()")
    assert "try{initPremiumInteractions()}catch(e){console.warn('Review Defense visual interaction init failed',e)}" in block


def test_public_routes_have_one_boot_owner():
    public = (ROOT / "frontend/assets/public.js").read_text()
    app = (ROOT / "frontend/assets/app.js").read_text()
    assert "function bootPublicRoute()" in public
    assert "showPublicPage(page,false);" in public
    assert "const publicPage=typeof publicPathPage" not in app
    assert "Object.values(PUBLIC_ROUTES)" not in app
    assert "showPublicPage(publicPage||'home',false)" not in app
