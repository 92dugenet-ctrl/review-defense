from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_bilingual_locale_layer_is_loaded_by_public_shells():
    for name in ("frontend/index.html", "frontend/landing.html"):
        text = (ROOT / name).read_text()
        assert '/assets/i18n.js?v=1' in text


def test_bilingual_locale_layer_has_language_switch_and_dynamic_translation():
    text = (ROOT / "frontend/assets/i18n.js").read_text()
    assert "ReviewDefenseI18n" in text
    assert "rd-language-switcher" in text
    assert "MutationObserver" in text
    assert "localStorage.setItem(KEY" in text
    assert "document.documentElement.lang='en'" in text


def test_bilingual_locale_styles_are_available():
    for name in ("frontend/assets/public.css", "frontend/assets/app.css"):
        text = (ROOT / name).read_text()
        assert "#rd-language-switcher" in text
