#!/usr/bin/env python3
"""V6.33 Release Candidate / Production Readiness Gate.

Deterministic, non-destructive gate. It validates repository contracts, runs the
full regression suite and compile check, and records an auditable JSON report.
It never deploys, migrates a live database, contacts Google, removes/reports/
replies to reviews, or performs production remediation.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.40"


def run(cmd: list[str], timeout: int = 300) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode, p.stdout


def contract_checks() -> dict[str, object]:
    checks: dict[str, object] = {}
    api = (ROOT / "src/api_server.py").read_text()
    release = (ROOT / "scripts/release_check.py").read_text()
    dr = (ROOT / "scripts/dr_validate.py").read_text()
    js = (ROOT / "frontend/assets/app.js").read_text()
    checks["version"] = VERSION in api
    checks["release_check_present"] = (ROOT / "scripts/release_check.py").is_file()
    checks["dr_validator_present"] = (ROOT / "scripts/dr_validate.py").is_file()
    checks["browser_e2e_present"] = (ROOT / "scripts/browser_e2e.py").is_file()
    checks["staging_check_present"] = (ROOT / "scripts/staging_check.py").is_file()
    checks["staging_certification_present"] = (ROOT / "scripts/staging_certification.py").is_file()
    checks["docker_runtime_present"] = (ROOT / "Dockerfile").is_file() and (ROOT / "docker-compose.staging.yml").is_file()
    checks["security_headers"] = all(x in (ROOT / "src/deployment.py").read_text() for x in ["object-src 'none'", "frame-ancestors 'none'", "connect-src 'self'"])
    checks["human_approval_gate"] = "Confirmer l’approbation humaine" in js and "Aucune action externe ne sera exécutée" in js
    checks["google_external_block"] = not any(x in js for x in ["google.com", "googleapis.com"])
    checks["dr_source_is_explicit"] = "REVIEW_DEFENSE_TEST_DATABASE_URL" in dr and "DATABASE_URL fallback" in dr
    checks["dr_confirmation"] = "--confirm" in dr and "restore target must be different" in dr
    checks["no_autonomous_google"] = all(x not in api.lower() for x in ["delete review", "report review", "reply review"])
    checks["release_check_is_static"] = "release check: PASS" in release
    checks["staging_certification_contract"] = "CONTRACT-PASS-NOT-LIVE-CERTIFIED" in (ROOT / "scripts/staging_certification.py").read_text()
    checks["all"] = all(v is True for k, v in checks.items() if k != "all")
    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("artifacts/v6.33-release-candidate.json"))
    ap.add_argument("--skip-tests", action="store_true", help="contract-only check; not a production readiness PASS")
    args = ap.parse_args()
    args.output = args.output if args.output.is_absolute() else ROOT / args.output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {"version": VERSION, "started_at": datetime.now(timezone.utc).isoformat(), "status": "NO-GO"}
    report["contracts"] = contract_checks()
    if not report["contracts"]["all"]:
        report["error"] = "one or more readiness contracts failed"
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True)); return 1
    if args.skip_tests:
        report["status"] = "CONTRACT-PASS-NOT-RELEASE-GO"
        report["limitation"] = "full regression suite was intentionally skipped"
    else:
        rc, out = run([sys.executable, "-m", "pytest", "-q"], timeout=600)
        report["pytest"] = {"returncode": rc, "tail": out[-12000:]}
        if rc != 0:
            report["error"] = "regression suite failed"
        else:
            rc2, out2 = run([sys.executable, "-m", "compileall", "-q", "src", "tests"])
            report["compileall"] = {"returncode": rc2, "output": out2[-4000:]}
            rc3, out3 = run([sys.executable, "scripts/release_check.py"])
            report["release_check"] = {"returncode": rc3, "output": out3[-6000:]}
            if rc2 == 0 and rc3 == 0:
                report["status"] = "PASS"
            else:
                report["error"] = "compile or release check failed"
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__": raise SystemExit(main())
