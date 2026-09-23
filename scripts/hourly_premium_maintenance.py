#!/usr/bin/env python3
"""Hourly bounded premium-site maintenance for Review Defense.

Only touches the public commercial layer. It never changes authentication,
business logic, database code, or external Google actions.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "frontend/landing.html"
HOME_CSS = ROOT / "frontend/assets/home.css"
REPORT = ROOT / "artifacts/hourly-premium-maintenance.json"


def run(*cmd: str) -> str:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()


def main() -> int:
    LANDING.parent.mkdir(parents=True, exist_ok=True)
    HOME_CSS.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    changes: list[str] = []
    landing = LANDING.read_text(encoding="utf-8")
    css = HOME_CSS.read_text(encoding="utf-8")

    # Keep the public surface self-contained: no remote Google font dependency.
    before = landing
    landing = re.sub(r'^\s*<link[^>]+fonts\.googleapis\.com[^>]*>\s*\n?', '', landing, flags=re.I | re.M)
    landing = re.sub(r'^\s*<link[^>]+fonts\.gstatic\.com[^>]*>\s*\n?', '', landing, flags=re.I | re.M)
    if landing != before:
        changes.append("removed remote Google Fonts tags from landing.html")

    # Preserve the browser/UAT public commercial boundary.
    if 'class="hero rd-home-hero"' not in landing and 'class="hero ' in landing:
        landing = landing.replace('class="hero ', 'class="hero rd-home-hero ', 1)
        changes.append("restored rd-home-hero compatibility class")

    if 'id="public-login"' not in landing:
        landing, n = re.subn(r'(<a\b[^>]*href="/app"[^>]*)(>)', r'\1 id="public-login"\2', landing, count=1)
        if n:
            changes.append("restored public-login hook")

    # Premium typography without requiring a network font.
    css_before = css
    css = css.replace(
        'font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
        'font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
        1,
    )
    if css != css_before:
        changes.append("normalized local-first premium font stack")

    polish = """
/* Hourly premium guardrails: accessibility + rendering polish. */
.rd-home{ -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; text-rendering:optimizeLegibility; }
.rd-home ::selection{background:#146cf0;color:#fff}
.rd-home a:focus-visible,.rd-home button:focus-visible,.rd-home input:focus-visible,.rd-home textarea:focus-visible,.rd-home summary:focus-visible{outline:3px solid rgba(20,108,240,.35);outline-offset:3px}
@media (prefers-reduced-motion:no-preference){html:has(.rd-home){scroll-behavior:smooth}}
"""
if "Hourly premium guardrails" not in css:
        css = css.rstrip() + "\n" + polish
        changes.append("added premium accessibility/focus/rendering guardrails")

    LANDING.write_text(landing, encoding="utf-8")
    HOME_CSS.write_text(css, encoding="utf-8")

    report = {
        "version": "6.40",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": "public-commercial-layer-only",
        "changes": changes,
        "working_tree": run("git", "status", "--short"),
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if changes:
        subprocess.run(["git", "config", "user.name", "review-defense-premium-bot"], cwd=ROOT, check=False)
        subprocess.run(["git", "config", "user.email", "review-defense-premium-bot@users.noreply.github.com"], cwd=ROOT, check=False)
        subprocess.run(["git", "add", "frontend/landing.html", "frontend/assets/home.css"], cwd=ROOT, check=False)
        subprocess.run(
            ["git", "commit", "-m", "chore: hourly premium site maintenance"],
            cwd=ROOT,
            check=False,
        )

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
