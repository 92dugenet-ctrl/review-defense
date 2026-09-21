from src.seo_content import PAGES
from src.seo_renderer import is_seo_path, render_page, sitemap, robots

def test_v639_seo_pack_is_complete():
    assert len(PAGES) == 62
    paths=["/"+slug+"/" for slug,_,_ in PAGES]
    assert len(paths)==len(set(paths))
    assert "/suppression-avis-google/" in paths
    assert "/analyse-avis-google/" in paths

def test_v639_unique_metadata_and_canonical():
    pages=[render_page("/"+slug+"/").decode() for slug,_,_ in PAGES]
    assert all('rel="canonical"' in p for p in pages)
    assert all('name="description"' in p for p in pages)
    assert all('index,follow' in p for p in pages)
    assert len({p.split('<title>',1)[1].split('</title>',1)[0] for p in pages}) == 62

def test_v639_structured_data_and_faq_are_visible():
    html=render_page('/faux-avis-google/').decode()
    assert 'BreadcrumbList' in html
    assert 'FAQPage' in html
    assert 'Questions fréquentes' in html
    assert '/analyse-avis-google/' in html
    assert 'pas automatiquement supprimable' in html

def test_v639_sitemap_and_robots():
    sm=sitemap().decode(); rb=robots().decode()
    assert sm.count('<url>') == 67
    assert 'sitemap.xml' in rb
    assert 'Disallow: /app' in rb
    assert 'Disallow: /v1/' in rb
