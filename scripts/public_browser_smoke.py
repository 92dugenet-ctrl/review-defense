#!/usr/bin/env python3
"""V6.40 public-site browser smoke certification.

Starts the reference WSGI application locally and exercises the seven public
marketing routes in a real Chromium browser. This is intentionally independent
from the live staging/E2E certification: it catches blank pages, client-side
routing regressions and uncaught browser errors before deployment.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wsgiref.simple_server import WSGIRequestHandler, make_server  # noqa: E402

from wsgi import app  # noqa: E402

ROUTES = {
    "/": "Review Defense",
    "/produit/": "Produit Review Defense",
    "/comment-ca-marche/": "Comment ça marche",
    "/services/": "Services B2B",
    "/tarifs/": "Tarifs",
    "/ressources/": "Ressources",
    "/contact/": "Contact",
}


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *_args):
        return


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright is required", file=sys.stderr)
        return 2

    server = make_server("127.0.0.1", 8765, app, handler_class=QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    failures = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            console_errors = []
            page_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            for route, expected in ROUTES.items():
                console_errors.clear()
                page_errors.clear()
                response = page.goto(f"http://127.0.0.1:8765{route}", wait_until="networkidle")
                if response is None or response.status != 200:
                    failures.append(f"{route}: HTTP {response.status if response else 'none'}")
                    continue

                title = page.title()
                body_text = page.locator("body").inner_text()
                if not body_text.strip():
                    failures.append(f"{route}: blank body")
                if expected not in body_text:
                    failures.append(f"{route}: expected visible text missing: {expected}")
                if "Review Defense" not in title and route != "/":
                    failures.append(f"{route}: unexpected title: {title}")
                if console_errors:
                    failures.append(f"{route}: console errors: {console_errors[:3]}")
                if page_errors:
                    failures.append(f"{route}: uncaught page errors: {page_errors[:3]}")

            # Exercise browser history and the client-side navigation contract.
            page.goto("http://127.0.0.1:8765/", wait_until="networkidle")
            page.locator('button[data-public="services"]').click()
            page.wait_for_url("**/services/")
            if "Services" not in page.locator("body").inner_text():
                failures.append("navigation: services page did not render")
            page.go_back(wait_until="networkidle")
            if not page.url.endswith("/") or "Reprenez le contrôle" not in page.locator("body").inner_text():
                failures.append("navigation: browser back did not restore homepage")
            page.go_forward(wait_until="networkidle")
            if not page.url.endswith("/services/"):
                failures.append("navigation: browser forward did not restore services")

            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    if failures:
        print("browser smoke: FAIL")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print(f"browser smoke: PASS ({len(ROUTES)} routes + history)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
