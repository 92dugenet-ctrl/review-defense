from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("deploy_staging", ROOT / "scripts/deploy_staging.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def test_deployment_workflow_contract_passes():
    checks = mod.workflow_checks()
    assert all(checks.values()), checks


def test_deployment_uses_ecloudserv_webhook_and_optional_https_certification():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    assert "ecloudserv-staging:" in workflow
    assert "Verify eCloudServ webhook deployment" in workflow
    assert "scripts/staging_certification.py --live" in workflow
    assert "STAGING_BASE_URL" in workflow


def test_deployment_has_no_ssh_dependency():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    assert "STAGING_SSH_" not in workflow
    assert "ssh -i" not in workflow
    assert "scp -i" not in workflow
    assert "rollback-staging:" not in workflow


def test_deployment_does_not_execute_google_actions():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text().lower()
    assert "googleapis.com" not in workflow
    assert "google.com" not in workflow
