from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("github_staging", ROOT / "scripts/github_staging_contract.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def test_github_staging_contract_passes():
    result = mod.checks()
    assert result["all"] is True if "all" in result else all(result.values())


def test_workflow_is_read_only_and_regression_gated():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    assert "contents: read" in workflow
    assert "pytest -q" in workflow
    assert "python scripts/release_check.py" in workflow


def test_live_certification_requires_manual_dispatch():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "staging_url:" in workflow
    assert "--live" in workflow


def test_no_github_action_can_execute_google_operation():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text().lower()
    assert "googleapis.com" not in workflow
    assert "google.com" not in workflow
