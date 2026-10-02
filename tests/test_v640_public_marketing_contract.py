from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_JS = ROOT / "frontend" / "assets" / "public.js"


def test_public_marketing_does_not_promise_platform_removal():
    text = PUBLIC_JS.read_text(encoding="utf-8")
    assert "vous accompagne dans leur suppression sur Google, Tripadvisor, Yelp" not in text
    assert "Aucune suppression garantie" in text
    assert "La décision finale appartient toujours à la plateforme" in text


def test_public_marketing_does_not_publish_unverified_customer_metrics():
    text = PUBLIC_JS.read_text(encoding="utf-8")
    for marker in ("250+", "4,8/5", "70 %", "−60 %", "ACCOR", "BNP PARIBAS", "L’ORÉAL", "DECATHLON"):
        assert marker not in text


def test_public_marketing_keeps_human_control_boundary():
    text = PUBLIC_JS.read_text(encoding="utf-8")
    assert "Structurez votre dossier avant toute démarche externe." in text
