from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_JS = (ROOT / "frontend/assets/public.js").read_text(encoding="utf-8")


def test_p3_public_navigation_has_timeout_and_retryable_failure():
    assert "let __publicNavigationToken=0;" in PUBLIC_JS
    assert "window.setTimeout" in PUBLIC_JS
    assert "8000" in PUBLIC_JS
    assert "__seoArticlesPromise=null" in PUBLIC_JS
    assert "publicLoadError()" in PUBLIC_JS
    assert 'role="alert"' in PUBLIC_JS
    assert "aria-live=\\\"assertive\\\"" in PUBLIC_JS


def test_p3_public_navigation_ignores_stale_async_render():
    assert "const navigationToken=++__publicNavigationToken;" in PUBLIC_JS
    assert "if(navigationToken!==__publicNavigationToken)return;" in PUBLIC_JS
    assert PUBLIC_JS.count("if(navigationToken!==__publicNavigationToken)return;") >= 2
