from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_v640_root_is_commercial_homepage():
    js=(ROOT/"frontend/assets/public.js").read_text(encoding="utf-8")
    assert "function homePage()" in js
    home=js[js.index("function homePage()"):js.index("function featuresPage()")]
    for marker in ["Analyser un avis", "TARIFS", "SERVICES", "HUMAN APPROVAL", "Tout le dossier", "Review Defense"]:
        assert marker in home
    assert "décision finale appartient" in home

def test_v640_commercial_header_primary_cta_goes_to_analysis():
    js=(ROOT/"frontend/assets/public.js").read_text(encoding="utf-8")
    assert 'id="public-cta">Analyser un avis' in js
    assert "location.href='/analyse-avis-google/'" in js

def test_v640_homepage_does_not_present_app_as_root_destination():
    js=(ROOT/"frontend/assets/public.js").read_text(encoding="utf-8")
    home=js[js.index("function homePage()"):js.index("function featuresPage()")]
    assert "location.href='/app'" not in home
