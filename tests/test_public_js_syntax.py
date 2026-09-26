from pathlib import Path
import shutil
import subprocess

def test_public_js_is_valid_javascript():
    node = shutil.which("node")
    if not node:
        return
    path = Path(__file__).resolve().parents[1] / "frontend" / "assets" / "public.js"
    result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

ROOT = Path(__file__).resolve().parents[1]


def test_seo_article_keys_are_unique_and_match_server_pack():
    import re

    frontend = (ROOT / "frontend/assets/seo-articles.js").read_text(encoding="utf-8")
    server = (ROOT / "src/seo_content.py").read_text(encoding="utf-8")
    frontend_keys = re.findall(r'^\s*"([^"]+)":\s*\{', frontend, flags=re.MULTILINE)
    server_keys = re.findall(r'^\("([^"]+)"', server, flags=re.MULTILINE)

    assert len(frontend_keys) == len(set(frontend_keys))
    assert set(frontend_keys) == set(server_keys) - {
        "analyse-avis-google",
        "service-suppression-avis-google",
        "agence-suppression-avis-google",
        "expert-suppression-avis-google",
        "faire-supprimer-avis-google",
        "prix-suppression-avis-google",
    }
