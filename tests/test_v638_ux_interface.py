from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_v638_public_premium_interface():
    html=(ROOT/'frontend/index.html').read_text(); pub=(ROOT/'frontend/assets/public.js').read_text(); css=(ROOT/'frontend/assets/public.css').read_text(); js=(ROOT/'frontend/assets/app.js').read_text()
    assert '/assets/public.js' in html
    for x in ['showPublicPage','Fonctionnalités','Tarifs','Ressources','contactPage','pricingPage']: assert x in pub
    for x in ['public-header','hero-section','pricing-grid','feature-grid','contact-layout','@media']: assert x in css
    assert "location.pathname==='/app'" in js

def test_v638_public_ui_keeps_external_action_boundary():
    pub=(ROOT/'frontend/assets/public.js').read_text(); js=(ROOT/'frontend/assets/app.js').read_text()
    assert 'googleapis.com' not in pub+js
    assert 'Aucune action externe ne sera exécutée' in js
    assert "confirm('Figer le dossier" in js
