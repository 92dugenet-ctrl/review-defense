from __future__ import annotations

import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
ASSETS = FRONTEND / "assets"


def test_new_frontend_contains_only_intended_public_assets():
    expected = {FRONTEND / "index.html", FRONTEND / "landing.html", ASSETS / "public.js", ASSETS / "public.css", ASSETS / "seo-articles.js"}
    actual = {p for p in FRONTEND.rglob("*") if p.is_file()}
    assert actual == expected


def test_public_javascript_passes_node_syntax_check():
    result = subprocess.run(["node", "--check", str(ASSETS / "public.js")], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_public_shell_does_not_load_legacy_frontend_runtime():
    combined = (FRONTEND / "index.html").read_text(encoding="utf-8") + (FRONTEND / "landing.html").read_text(encoding="utf-8")
    for legacy in ("app.js", "app.css", "console-router.js", "console-components.js", "billing.js", "i18n.js", "seo-renderer.js"):
        assert legacy not in combined
    assert "/assets/public.js?v=6711" in combined
    assert "/assets/public.css?v=6711" in combined


def test_public_runtime_declares_new_routes_and_human_control():
    text = (ASSETS / "public.js").read_text(encoding="utf-8")
    for route in ("/", "/produit/", "/comment-ca-marche/", "/services/", "/tarifs/", "/ressources/", "/contact/", "/analyse-avis-google/", "/ia-et-controle-humain/"):
        assert route in text
    assert "HUMAN APPROVAL REQUIRED" in text
    assert "La décision finale appartient toujours à la plateforme." in text
    assert "Aucune action externe n’a été déclenchée." in text
