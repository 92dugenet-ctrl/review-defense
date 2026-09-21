#!/usr/bin/env python3
"""V6.40 staging deployment verification and certification.

Contract-first and non-destructive. With STAGING_BASE_URL it performs bounded
live HTTPS checks. Without it, it validates that the repository contains the
complete staging deployment contract but never claims live certification.
"""
from __future__ import annotations
import argparse, json, os, re, ssl, sys, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.40"


def contract_checks() -> dict[str, bool]:
    compose = (ROOT / "docker-compose.staging.yml").read_text()
    caddy = (ROOT / "Caddyfile").read_text()
    env = (ROOT / ".env.example").read_text()
    api = (ROOT / "src/api_server.py").read_text()
    checks = {
        "version": '"6.40"' in api,
        "staging_compose": (ROOT / "docker-compose.staging.yml").is_file(),
        "dockerfile": (ROOT / "Dockerfile").is_file(),
        "caddyfile": (ROOT / "Caddyfile").is_file(),
        "staging_smoke": (ROOT / "scripts/staging_check.py").is_file(),
        "browser_e2e": (ROOT / "scripts/browser_e2e.py").is_file(),
        "dr_validator": (ROOT / "scripts/dr_validate.py").is_file(),
        "postgres_healthcheck": "pg_isready" in compose,
        "migrations_before_app": "python scripts/migrate.py" in compose,
        "https_only_smoke": 'STAGING_BASE_URL' in (ROOT / "scripts/staging_check.py").read_text() and 'https://' in (ROOT / "scripts/staging_check.py").read_text(),
        "tls_caddy": "tls" in caddy.lower() and ":443" in compose,
        "public_base_url_required": "REVIEW_DEFENSE_PUBLIC_BASE_URL" in compose and "REVIEW_DEFENSE_PUBLIC_BASE_URL" in env,
        "mfa_key_required": "REVIEW_DEFENSE_MFA_ENCRYPTION_KEY" in compose,
        "trust_proxy": 'TRUST_PROXY: "true"' in compose,
        "secure_headers": 'SECURE_HEADERS: "true"' in compose,
        "two_workers": "--workers 2" in compose,
        "no_google_frontend": not any(x in (ROOT / "frontend/assets/app.js").read_text() for x in ["google.com", "googleapis.com"]),
    }
    checks["all"] = all(v for k, v in checks.items() if k != "all")
    return checks


def fetch(base: str, path: str) -> tuple[int, dict, dict[str, str]]:
    req = urllib.request.Request(base.rstrip('/') + path, headers={"Accept": "application/json"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        raw = r.read().decode("utf-8", errors="replace")
        try: payload = json.loads(raw)
        except json.JSONDecodeError: payload = {"raw": raw[:2000]}
        return r.status, payload, {k.lower(): v for k, v in r.headers.items()}


def live_checks(base: str) -> dict[str, object]:
    if not base.startswith("https://"):
        raise ValueError("STAGING_BASE_URL must use HTTPS")
    result: dict[str, object] = {"base_url": base.rstrip('/')}
    status, health, headers = fetch(base, "/health")
    result["health"] = {"status": status, "version": health.get("version"), "service": health.get("service")}
    if status != 200 or health.get("version") != VERSION:
        raise RuntimeError(f"health check failed: {status} {health}")
    status, ready, ready_headers = fetch(base, "/ready")
    result["ready"] = {"status": status, "payload": ready}
    if status != 200 or ready.get("status") != "ready":
        raise RuntimeError(f"readiness check failed: {status} {ready}")
    merged = {**headers, **ready_headers}
    required_headers = ["content-security-policy", "x-content-type-options", "x-frame-options", "referrer-policy"]
    result["security_headers"] = {h: h in merged for h in required_headers}
    if not all(result["security_headers"].values()):
        raise RuntimeError("required security headers missing")
    # Metrics are protected in production; an unauthenticated request must not expose telemetry.
    try:
        ms, _, _ = fetch(base, "/metrics")
        result["metrics_unauthenticated"] = ms
        if ms == 200:
            raise RuntimeError("production metrics endpoint is publicly exposed")
    except urllib.error.HTTPError as e:
        result["metrics_unauthenticated"] = e.code
        if e.code not in (401, 403, 404):
            raise RuntimeError(f"unexpected metrics response: {e.code}")
    result["certified_live"] = True
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("artifacts/v6.40-staging-certification.json"))
    ap.add_argument("--live", action="store_true", help="require live STAGING_BASE_URL certification")
    args = ap.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"version": VERSION, "started_at": datetime.now(timezone.utc).isoformat(), "status": "NO-GO"}
    report["contracts"] = contract_checks()
    if not report["contracts"]["all"]:
        report["error"] = "staging deployment contract failed"
    else:
        base = os.environ.get("STAGING_BASE_URL", "").strip()
        if args.live or base:
            if not base:
                report["error"] = "--live requires STAGING_BASE_URL"
            else:
                try:
                    report["live"] = live_checks(base)
                    report["status"] = "CERTIFIED"
                except Exception as exc:
                    report["error"] = str(exc)
        else:
            report["status"] = "CONTRACT-PASS-NOT-LIVE-CERTIFIED"
            report["limitation"] = "no STAGING_BASE_URL was supplied; no live infrastructure was exercised"
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in ("CERTIFIED", "CONTRACT-PASS-NOT-LIVE-CERTIFIED") else 1

if __name__ == "__main__": raise SystemExit(main())
