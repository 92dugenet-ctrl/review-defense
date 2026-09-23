from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMERCIAL = ["/", "/produit/", "/comment-ca-marche/", "/services/", "/tarifs/", "/ressources/", "/contact/"]


def test_server_renders_all_commercial_routes():
    seo = (ROOT / "src/seo_site.py").read_text(encoding="utf-8")
    for route in COMMERCIAL:
        assert '"' + route + '":{' in seo
    assert "def _commercial_html(path):" in seo
    assert "if path in COMMERCIAL:" in seo


def test_commercial_pages_are_crawlable_and_canonical():
    seo = (ROOT / "src/seo_site.py").read_text(encoding="utf-8")
    assert 'name="robots" content="index,follow"' in seo
    assert 'rel="canonical"' in seo
    assert 'application/ld+json' in seo


def test_sitemap_includes_commercial_routes_and_seo_network():
    seo = (ROOT / "src/seo_site.py").read_text(encoding="utf-8")
    assert '[{"path":"/"}]+[{"path":x} for x in COMMERCIAL if x!="/"]+pages' in seo
    assert '"analyse-avis-google"' in seo
    assert '"faux-avis-google"' in seo
    assert '"signaler-un-avis-google"' in seo


def test_seo_network_uses_clean_commercial_urls():
    seo = (ROOT / "src/seo_site.py").read_text(encoding="utf-8")
    for old in ["/?page=features", "?page=how", "?page=pricing", "?page=resources"]:
        assert old not in seo
    for route in ["/produit/", "/comment-ca-marche/", "/tarifs/", "/ressources/", "/contact/"]:
        assert route in seo


def test_conversion_routes_to_analysis_not_automatic_google_action():
    seo = (ROOT / "src/seo_site.py").read_text(encoding="utf-8")
    assert 'href="/analyse-avis-google/"' in seo
    assert "Aucune action Google automatique" in seo
    assert "La décision finale appartient toujours à la plateforme concernée." in seo
