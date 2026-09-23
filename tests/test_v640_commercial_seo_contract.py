from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v640_clean_commercial_routes_are_declared():
    app = (ROOT / "frontend/assets/app.js").read_text(encoding="utf-8")
    public = (ROOT / "frontend/assets/public.js").read_text(encoding="utf-8")
    for path in ["/", "/produit/", "/comment-ca-marche/", "/services/", "/tarifs/", "/ressources/", "/contact/"]:
        assert path in app or path in public
    assert "const PUBLIC_ROUTES" in public


def test_v640_sitemap_contains_commercial_routes():
    seo = (ROOT / "src/seo_renderer.py").read_text(encoding="utf-8")
    for path in ["/produit/", "/comment-ca-marche/", "/services/", "/tarifs/", "/ressources/", "/contact/"]:
        assert 'BASE_URL+"' + path + '"' in seo


def test_v640_commercial_meta_is_defined():
    public = (ROOT / "frontend/assets/public.js").read_text(encoding="utf-8")
    assert "PUBLIC_META" in public
    assert "Produit Review Defense" in public
    assert "Tarifs | Review Defense" in public
