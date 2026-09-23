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
