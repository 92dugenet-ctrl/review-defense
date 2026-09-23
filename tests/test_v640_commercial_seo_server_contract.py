from src import seo_site

COMMERCIAL = ["/", "/produit/", "/comment-ca-marche/", "/services/", "/tarifs/", "/ressources/", "/contact/"]


def test_server_renders_all_commercial_routes():
    assert list(seo_site.COMMERCIAL) == COMMERCIAL
    for route in COMMERCIAL:
        status, headers, body = seo_site.render(route)
        assert status == 200
        assert headers["Content-Type"].startswith("text/html")
        assert b"Review Defense" in body


def test_commercial_pages_are_crawlable_and_canonical():
    for route in COMMERCIAL:
        _, _, body = seo_site.render(route)
        text = body.decode()
        assert 'name="robots" content="index,follow"' in text
        assert 'rel="canonical"' in text
        assert 'application/ld+json' in text


def test_sitemap_includes_commercial_routes_and_seo_network():
    _, _, body = seo_site.render("/sitemap.xml")
    xml = body.decode()
    assert xml.count("<url>") == 69
    for route in COMMERCIAL:
        assert route in xml
    for route in ["/analyse-avis-google/", "/faux-avis-google/", "/signaler-un-avis-google/"]:
        assert route in xml


def test_seo_network_uses_clean_commercial_urls():
    _, _, body = seo_site.render("/faux-avis-google/")
    text = body.decode()
    for old in ["/?page=features", "?page=how", "?page=pricing", "?page=resources"]:
        assert old not in text
    for route in ["/produit/", "/comment-ca-marche/", "/services/", "/tarifs/", "/ressources/", "/contact/"]:
        assert route in text


def test_conversion_page_has_form_and_tracking_contract():
    _, _, body = seo_site.render("/analyse-avis-google/")
    text = body.decode()
    assert 'id="rd-analysis-form"' in text
    assert "analysis_start" in text
    assert "analysis_submit" in text
    assert "Aucune action Google n’est exécutée automatiquement." in text
    assert "la plateforme concernée" in text


def test_legacy_commercial_query_urls_redirect():
    from wsgi import app
    captured = {}
    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)
    body = app({"PATH_INFO": "/", "QUERY_STRING": "page=pricing"}, start_response)
    assert captured["status"] == "301 Moved Permanently"
    assert captured["headers"]["Location"] == "/tarifs/"
    assert body == [b""]
