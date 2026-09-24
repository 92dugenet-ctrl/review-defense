#!/usr/bin/env python3
"""V6.40 live HTTPS/auth/MFA/browser UAT for a dedicated staging account."""
from __future__ import annotations
import argparse, json, os, sys, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def api_login(base: str, email: str, org: str, password: str, mfa_code: str | None = None):
    body = {"email": email, "organization_id": org, "password": password}
    if mfa_code:
        body["mfa_code"] = mfa_code
    req = urllib.request.Request(
        base.rstrip('/') + '/v1/auth/login',
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:1000]}
        return e.code, payload

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=os.getenv("STAGING_BASE_URL", ""))
    ap.add_argument("--output", type=Path, default=ROOT / "artifacts/v6.40-live-e2e.json")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")
    required = ["E2E_EMAIL", "E2E_PASSWORD", "E2E_ORGANIZATION_ID"]
    missing = [x for x in required if not os.getenv(x)]
    report = {
        "version": "6.40",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "NO-GO",
        "base_url": base,
        "uat_scope": ["AUTH", "DASHBOARD", "REVIEWS", "CASES", "HUMAN_GATE", "BROWSER_SECURITY"],
    }

    if not base.startswith("https://"):
        report["error"] = "STAGING_BASE_URL must use HTTPS"
    elif missing:
        report["error"] = "missing required E2E secrets: " + ", ".join(missing)
    else:
        email = os.environ["E2E_EMAIL"]
        password = os.environ["E2E_PASSWORD"]
        org = os.environ["E2E_ORGANIZATION_ID"]
        mfa_secret = os.getenv("E2E_MFA_SECRET", "")
        access_token = None

        if mfa_secret:
            status, payload = api_login(base, email, org, password)
            report["mfa_enforcement_without_code"] = {"status": status, "error": payload.get("error")}
            if status != 401:
                report["error"] = "MFA-enabled staging account accepted password-only login"
            else:
                from src.mfa import totp_code
                status, payload = api_login(base, email, org, password, totp_code(mfa_secret))
                report["mfa_login"] = {"status": status}
                if status != 200 or not payload.get("access_token"):
                    report["error"] = "MFA login failed"
                else:
                    access_token = payload["access_token"]
        else:
            status, payload = api_login(base, email, org, password)
            report["password_login"] = {"status": status}
            if status != 200 or not payload.get("access_token"):
                report["error"] = "staging password login failed"
            else:
                access_token = payload["access_token"]

        if "error" not in report:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                    page = browser.new_page()
                    browser_errors = []
                    browser_console = []
                    asset_responses = []
                    page.on("pageerror", lambda exc: browser_errors.append(str(exc)))
                    page.on("console", lambda msg: browser_console.append(f"{msg.type}: {msg.text}"))
                    page.on(
                        "response",
                        lambda response: asset_responses.append({
                            "url": response.url,
                            "status": response.status,
                            "content_type": response.headers.get("content-type", ""),
                        }) if "/assets/" in response.url else None,
                    )

                    # Public commercialization boundary: the root URL must open the commercial landing page,
                    # and the landing page must provide a direct path into the authenticated interface.
                    page.goto(base + "/", wait_until="networkidle")
                    page.wait_for_selector(".rd-home-hero", timeout=10000)
                    landing_text = page.locator("body").inner_text()
                    if "Reprenez le contrôle de" not in landing_text or "Analyser un avis" not in landing_text:
                        report["root_diagnostic"] = {
                            "url": page.url,
                            "title": page.title(),
                            "ready_state": page.evaluate("document.readyState"),
                            "body_text": landing_text[:5000],
                            "app_root_html": page.locator("#app").inner_html()[:5000] if page.locator("#app").count() else "",
                            "script_srcs": page.locator("script").evaluate_all("(els) => els.map(e => e.src)"),
                            "page_errors": browser_errors[-20:],
                            "console": browser_console[-50:],
                            "asset_responses": [x for x in asset_responses if "/assets/app.js" in x["url"] or "/assets/public.js" in x["url"] or "/assets/public.css" in x["url"]],
                        }
                        raise AssertionError("public commercial landing page is not served at the root URL")
                    page.locator("#public-login").click()
                    page.wait_for_selector("#login", timeout=10000)
                    report["public_commercial_landing"] = {
                        "status": "PASS",
                        "root_url": base + "/",
                        "login_cta": "PASS",
                    }
                    # The API login above creates the real server-side session, but
                    # the browser has its own localStorage token. Seed that browser
                    # context with the token returned by the authenticated API login
                    # before opening /app; this tests the actual multi-worker session
                    # restoration path rather than accidentally testing two unrelated
                    # clients.
                    if not access_token:
                        raise AssertionError("authenticated API login did not return an access token")
                    page.evaluate(
                        "(token) => localStorage.setItem('rd_token', token)",
                        access_token,
                    )
                    page.goto(base + "/app", wait_until="networkidle")
                    try:
                        page.wait_for_function(
                            "() => !!document.querySelector('.sidebar, #login')",
                            timeout=10000,
                        )
                    except Exception as exc:
                        report["browser_diagnostic"] = {
                            "stage": "initial_app_boot",
                            "url": page.url,
                            "title": page.title(),
                            "ready_state": page.evaluate("document.readyState"),
                            "body_text": page.locator("body").inner_text()[:4000],
                            "app_root_html": page.locator("#app").inner_html()[:4000] if page.locator("#app").count() else "",
                            "script_srcs": page.locator("script").evaluate_all("(els) => els.map(e => e.src)"),
                            "page_errors": browser_errors[-20:],
                            "console": browser_console[-50:],
                            "asset_responses": [
                                x for x in asset_responses
                                if "/assets/app.js" in x["url"] or "/assets/public.js" in x["url"] or "/assets/app.css" in x["url"]
                            ],
                        }
                        raise exc
                    if page.locator("#login").count() and page.locator("#login").is_visible():
                        report["browser_diagnostic"] = {
                            "stage": "initial_app_boot",
                            "reason": "app route opened the login screen instead of restoring the authenticated session",
                            "url": page.url,
                            "title": page.title(),
                            "ready_state": page.evaluate("document.readyState"),
                            "body_text": page.locator("body").inner_text()[:4000],
                            "page_errors": browser_errors[-20:],
                            "console": browser_console[-50:],
                            "asset_responses": [
                                x for x in asset_responses
                                if "/assets/app.js" in x["url"] or "/assets/public.js" in x["url"] or "/assets/app.css" in x["url"]
                            ],
                        }
                        raise AssertionError("authenticated browser session was not restored at /app")

                    # Session restoration succeeded. Continue directly with the authenticated
                    # console; do not perform a second login, which would invalidate the
                    # purpose of this multi-worker restoration test.
                    page.wait_for_selector(".sidebar", timeout=10000)
                    page.wait_for_selector("#console-sidebar", timeout=5000)
                    page.wait_for_selector("#content", timeout=5000)
                    page.wait_for_selector("#content .hero-grid", timeout=10000)

                    def view(label: str, expected_title: str, selector: str, fallback_markers: tuple[str, ...] = ()):
                        button = page.locator(f'#nav button[data-view="{label}"]')
                        if not button.count():
                            raise AssertionError(f"navigation item missing: {label}")
                        button.click()
                        page.wait_for_function(
                            "(title) => document.querySelector('#title')?.innerText === title",
                            arg=expected_title,
                            timeout=10000,
                        )
                        page.wait_for_selector(selector, timeout=10000)
                        text = page.locator("#content").inner_text()
                        if fallback_markers and not any(marker.lower() in text.lower() for marker in fallback_markers):
                            raise AssertionError(f"{label} view missing expected content markers: {fallback_markers}")
                        return text

                    dashboard_title = page.locator("#title").inner_text()
                    dashboard_text = page.locator("#content").inner_text()
                    reviews_text = view("reviews", "Avis", ".reviews-panel", ("Qualification des avis", "Inbox des avis"))
                    reviews_ok = page.locator(".reviews-panel").count() > 0
                    cases_text = view("cases", "Dossiers", ".cases-panel", ("Centre des dossiers", "File des dossiers"))
                    cases_ok = page.locator(".cases-panel").count() > 0
                    boundary_text = (dashboard_text + " " + reviews_text + " " + cases_text).lower()
                    approval_markers = ("validation humaine", "aucune action externe automatique", "contrôles humains", "action externe automatique", "revue humaine requise")
                    approval_marker = any(marker in boundary_text for marker in approval_markers)
                    if not approval_marker:
                        raise AssertionError("human-control boundary is not visible in the browser UAT")

                    resources = page.evaluate("performance.getEntriesByType('resource').map(x => x.name)")
                    forbidden = [u for u in resources if "googleapis.com" in u or "google.com" in u]
                    dashboard_ok = dashboard_title.strip() in {"Dashboard", "Vue d'ensemble", "Vue d’ensemble"} and bool(dashboard_text.strip())
                    browser_checks = {
                        "login": "PASS",
                        "dashboard": dashboard_ok,
                        "reviews": "PASS" if reviews_ok else "FAIL",
                        "cases": "PASS" if cases_ok else "FAIL",
                        "human_control_boundary": approval_marker,
                        "no_external_google": not forbidden,
                        "page_errors": browser_errors[-20:],
                        "page_error_policy": "diagnostic_only",
                    }
                    report["browser"] = browser_checks
                    core_browser_ok = all([dashboard_ok, reviews_ok, cases_ok, approval_marker, not forbidden])
                    if not core_browser_ok:
                        report["error"] = "browser UAT contract failed"

                    browser.close()
            except Exception as exc:
                report["error"] = f"browser UAT failed: {exc}"

        if "error" not in report:
            report["status"] = "CERTIFIED"

    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "CERTIFIED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
