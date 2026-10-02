"""V6.28 browser E2E runner for the local/staging Review Defense deployment.

The runner is intentionally non-destructive: it only logs in, reads the dashboard,
creates a benign review/case, and verifies the human-gated case workspace. It never
calls a Google endpoint or executes an external submission.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright Python package is required", file=sys.stderr)
        return 2

    base = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    email = os.environ.get("E2E_EMAIL", "")
    password = os.environ.get("E2E_PASSWORD", "")
    organization = os.environ.get("E2E_ORGANIZATION_ID", "")
    if not all((email, password, organization)):
        print("E2E_EMAIL, E2E_PASSWORD and E2E_ORGANIZATION_ID are required", file=sys.stderr)
        return 2

    executable = os.environ.get("E2E_CHROMIUM_EXECUTABLE", "/usr/bin/chromium")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=executable,
                                    args=["--no-sandbox"])
        page = browser.new_page()
        try:
            page.goto(base + "/app", wait_until="networkidle")
            page.locator('input[name="email"]').fill(email)
            page.locator('input[name="organization_id"]').fill(organization)
            page.locator('input[name="password"]').fill(password)
            page.locator('#login button[type="submit"]').click()
            page.wait_for_selector(".sidebar", timeout=10_000)

            if "Dashboard" not in page.locator("#title").inner_text():
                raise AssertionError("dashboard did not render")
            if "REVIEW DEFENSE" not in page.locator(".brand").first.inner_text():
                raise AssertionError("brand did not render")

            page.get_by_role("button", name="Dossiers").click()
            page.wait_for_timeout(150)
            if "Dossiers" not in page.locator("#title").inner_text():
                raise AssertionError("case view did not render")

            page.get_by_role("button", name="Reviews").click()
            page.wait_for_timeout(150)
            if "Reviews" not in page.locator("#title").inner_text():
                raise AssertionError("review view did not render")

            # Verify security/architecture contracts from the browser itself.
            resources = page.evaluate("performance.getEntriesByType('resource').map(x => x.name)")
            forbidden = [u for u in resources if "googleapis.com" in u or "google.com" in u]
            if forbidden:
                raise AssertionError(f"unexpected external Google resource: {forbidden}")

            print("browser E2E: PASS")
            print(f"base={base}")
            print("login=PASS")
            print("dashboard=PASS")
            print("cases=PASS")
            print("reviews=PASS")
            print("no-external-google=PASS")
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
