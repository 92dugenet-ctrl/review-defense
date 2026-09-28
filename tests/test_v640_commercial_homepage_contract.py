from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_JS = ROOT / "frontend/assets/public.js"


def test_v640_root_is_commercial_homepage():
    js = PUBLIC_JS.read_text(encoding="utf-8")
    assert "function homePage()" in js
    assert "function head(" in js
    assert "function cta()" in js

    home = js[js.index("function homePage()"):js.index("function featuresPage()")]
    assert "Review Defense" in home
    assert "HUMAN APPROVAL" in home
    assert "Tout le dossier" in home
    assert "décision finale appartient" in home

    # The homepage CTA is a public navigation action, not an application destination.
    cta = js[js.index("function cta()"):js.index("function homePage()")]
    assert 'data-r="analyze"' in cta
    assert "Commencer avec un avis" in cta

    routes = js[js.index("const R="):js.index("const N=")]
    assert 'analyze:"/analyse-avis-google/"' in routes
    assert 'product:"/produit/"' in routes
    assert 'pricing:"/tarifs/"' in routes
    assert 'teams:"/services/"' in routes


def test_v640_commercial_header_primary_cta_is_analysis_route():
    js = PUBLIC_JS.read_text(encoding="utf-8")
    header = js[js.index("function head("):js.index("function foot(")]
    assert 'id="public-cta"' in header
    assert 'data-r="analyze"' in header
    assert 'analyze:"/analyse-avis-google/"' in js


def test_v640_homepage_does_not_present_app_as_root_destination():
    js = PUBLIC_JS.read_text(encoding="utf-8")
    home = js[js.index("function homePage()"):js.index("function featuresPage()")]
    assert "location.href='/app'" not in home
