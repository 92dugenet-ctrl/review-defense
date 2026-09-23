from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]

def test_uat_pack_contains_47_scenarios():
    with (ROOT / "docs/UAT_V640_TEST_CASES.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 47
    assert len({r["id"] for r in rows}) == 47
    assert all(r["acceptance"].strip() for r in rows)

def test_uat_artifacts_are_present():
    required = [
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
        "scripts/uat_v640_certification.py",
    ]
    assert all((ROOT / p).is_file() for p in required)

def test_uat_seed_isolation_contract():
    text = (ROOT / "scripts/sandbox_seed.py").read_text(encoding="utf-8")
    assert "REVIEW_DEFENSE_TEST_DATABASE_URL" in text
    assert "Refusing to use DATABASE_URL" in text
    assert "external_actions_enabled" in text

def test_uat_human_gate_contract():
    release = (ROOT / "docs/UAT_V640_RELEASE_GATE.md").read_text(encoding="utf-8")
    assert "Human approval" in release
    assert "GO_STEP_4" in release
    assert "HOLD_STEP_3" in release
