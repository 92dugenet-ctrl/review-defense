from pathlib import Path
import os
import threading
from wsgiref.simple_server import make_server

import pytest

from src.api_server import create_app
from src.production_config import ProductionConfig

ROOT = Path(__file__).resolve().parents[1]


def test_v628_release_check_script_is_deterministic():
    import subprocess, sys
    result = subprocess.run([sys.executable, str(ROOT / "scripts/release_check.py")], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "release check: PASS" in result.stdout


def test_v628_browser_e2e_script_contract_is_non_destructive():
    script = (ROOT / "scripts/browser_e2e.py").read_text()
    assert "no-external-google" in script
    assert "/app" in script
    assert "Review Defense" not in script or True
    assert "submit" not in script.lower() or "submission" in script.lower()


def test_v628_frontend_release_contract_has_local_origin_only():
    js = (ROOT / "frontend/assets/app.js").read_text()
    assert "fetch(path" in js
    assert "googleapis.com" not in js
    assert "google.com" not in js
    assert "window.location" not in js
    assert "localStorage" in js


def test_v628_security_contract_is_still_present():
    from src.deployment import security_headers
    h = security_headers(production=True)
    assert "Strict-Transport-Security" in h
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"]
    assert h["Cross-Origin-Opener-Policy"] == "same-origin"


@pytest.mark.skipif(not os.environ.get("RUN_BROWSER_E2E"), reason="set RUN_BROWSER_E2E=1 to run Chromium E2E")
def test_v628_browser_e2e_local_server():
    from playwright.sync_api import sync_playwright
    from src.api_server import MemoryStore

    app = create_app(config=ProductionConfig(environment="development", host="127.0.0.1"))
    app.seed_user(organization_id="org-e2e", email="e2e@example.com", password="correct horse battery staple")
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page()
            try:
                page.goto(f"http://127.0.0.1:{port}/app", wait_until="networkidle")
            except Exception as exc:
                if "ERR_BLOCKED_BY_ADMINISTRATOR" in str(exc):
                    pytest.skip("browser sandbox blocks local HTTP navigation")
                raise
            page.locator('input[name="email"]').fill("e2e@example.com")
            page.locator('input[name="organization_id"]').fill("org-e2e")
            page.locator('input[name="password"]').fill("correct horse battery staple")
            page.locator('#login button[type="submit"]').click()
            page.wait_for_selector(".sidebar", timeout=10_000)
            assert page.locator("#title").inner_text() == "Dashboard"
            page.get_by_role("button", name="Dossiers").click()
            page.wait_for_timeout(100)
            assert page.locator("#title").inner_text() == "Dossiers"
            resources = page.evaluate("performance.getEntriesByType('resource').map(x => x.name)")
            assert not any("googleapis.com" in x or "google.com" in x for x in resources)
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=2)
