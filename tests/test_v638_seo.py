from src.seo_content import PAGES
from src.seo_renderer import is_seo_path, render_page, sitemap, robots

def test_v638_seo_index_contains_full_pack():
    assert len(PAGES) == 62
    assert any(slug == "suppression-avis-google" for slug, _, _ in PAGES)
    assert any(slug == "analyse-avis-google" for slug, _, _ in PAGES)

def test_v638_seo_renderer_has_unique_crawlable_pages():
    paths = ["/" + slug + "/" for slug, _, _ in PAGES]
    assert len(paths) == len(set(paths))
    assert all(is_seo_path(p) for p in paths)
    html = render_page("/faux-avis-google/").decode("utf-8")
    assert "<title>Faux avis Google" in html
    assert 'rel="canonical"' in html
    assert 'application/ld+json' in html
    assert "/analyse-avis-google/" in html

def test_v638_sitemap_and_robots_are_exposed():
    sm = sitemap().decode("utf-8")
    rb = robots().decode("utf-8")
    assert "sitemap.xml" in rb
    assert "suppression-avis-google" in sm
    assert "analyse-avis-google" in sm
    assert "/v1/" in rb
