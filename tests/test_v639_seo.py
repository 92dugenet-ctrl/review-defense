from src import seo_site


def test_v639_seo_pack_has_all_indexable_pages():
    pages=seo_site._pages()
    assert len(pages)==63
    assert any(p["path"]=="/suppression-avis-google/" for p in pages)
    assert any(p["path"]=="/analyse-avis-google/" and p["service"] for p in pages)


def test_v639_seo_pages_are_server_rendered_and_canonical():
    status,headers,body=seo_site.render("/suppression-avis-google/")
    text=body.decode()
    assert status==200
    assert headers["Content-Type"].startswith("text/html")
    assert '<link rel="canonical"' in text
    assert 'application/ld+json' in text
    assert 'BreadcrumbList' in text
    assert 'FAQPage' in text
    assert 'Suppression d&#x27;avis Google' in text


def test_v639_sitemap_and_robots_cover_public_seo_surface():
    status,_,body=seo_site.render("/sitemap.xml")
    xml=body.decode()
    assert status==200
    assert xml.count("<url>")==64
    assert "/suppression-avis-google/" in xml
    status,_,body=seo_site.render("/robots.txt")
    robots=body.decode()
    assert status==200
    assert "Sitemap:" in robots
    assert "Disallow: /app" in robots


def test_v639_seo_content_preserves_human_review_boundary():
    _,_,body=seo_site.render("/faux-avis-google/")
    text=body.decode()
    assert "aucune suppression n’est garantie" in text
    assert "la décision finale appartient à la plateforme" in text
    assert "Validation humaine" in text


def test_v639_unknown_path_is_not_captured_by_seo_router():
    assert seo_site.render("/does-not-exist/") is None
