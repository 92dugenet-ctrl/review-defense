#!/usr/bin/env python3
"""V6.40 UAT contract certification.

Static, deterministic and safe: this validates the complete UAT package and
its safety boundaries. It does not claim live staging certification.
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "docs/UAT_V640_TEST_CASES.csv"
EXPECTED = 47
REQUIRED = [
    "docs/UAT_V640_TEST_DATA_SPEC.md",
    "docs/UAT_V640_EXECUTION_PROTOCOL.md",
    "docs/UAT_V640_DEFECT_TRACEABILITY.md",
    "docs/UAT_V640_BROWSER_E2E_RUNBOOK.md",
    "docs/UAT_V640_RELEASE_GATE.md",
    "docs/UAT_V640_EVIDENCE_INDEX.md",
    "docs/UAT_V640_CAMPAIGN_CLOSURE.md",
    "docs/UAT_V640_ENVIRONMENT_READINESS.md",
    "docs/UAT_V640_BROWSER_UAT_PACKAGE.md",
    "docs/UAT_V640_EVIDENCE_DOSSIER.md",
    "docs/UAT_V640_FINAL_EXECUTION_RECORD.md",
    "docs/UAT_V640_FINAL_CHECKLIST.csv",
    "docs/UAT_V640_HANDOFF.md",
    "scripts/sandbox_seed.py",
    "scripts/uat_seed.py", "tests/fixtures/v640_uat_dataset.json",
    "scripts/staging_e2e.py",
    "scripts/browser_e2e.py",
]

def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    with SCENARIOS.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ids = [r["id"] for r in rows]
    checks = {
        "required_files": not missing,
        "scenario_count": len(rows) == EXPECTED,
        "unique_scenario_ids": len(ids) == len(set(ids)),
        "all_acceptance_text_present": all(r.get("acceptance","").strip() for r in rows),
        "test_database_boundary": "REVIEW_DEFENSE_TEST_DATABASE_URL" in (ROOT/"scripts/sandbox_seed.py").read_text(),
        "production_database_rejected": "Refusing to use DATABASE_URL" in (ROOT/"scripts/sandbox_seed.py").read_text(),
        "external_action_disabled": "external_actions_enabled" in (ROOT/"scripts/sandbox_seed.py").read_text(),
        "human_gate_documented": "Human approval" in (ROOT/"docs/UAT_V640_RELEASE_GATE.md").read_text(),
        "live_not_falsely_certified": ("not yet certified" in (ROOT/"docs/UAT_V640_FINAL_EXECUTION_RECORD.md").read_text().lower() or "not certified" in (ROOT/"docs/UAT_V640_FINAL_EXECUTION_RECORD.md").read_text().lower()),
        "final_report_manifest": (ROOT/"docs/UAT_V640_FINAL_REPORT_MANIFEST.md").is_file(),
    }
    checks["all"] = all(checks.values()) and not missing
    report = {"version":"6.40","status":"PASS" if checks["all"] else "FAIL",
              "scenario_count":len(rows),"expected":EXPECTED,"missing":missing,"checks":checks}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if checks["all"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
