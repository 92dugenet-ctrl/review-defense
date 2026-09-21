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


def test_deployment_uses_staging_environment_and_https_certification():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    assert "environment: staging" in workflow
    assert "scripts/staging_certification.py --live" in workflow
    assert "STAGING_BASE_URL" in workflow


def test_deployment_pins_ssh_host_keys():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    assert "STAGING_SSH_KNOWN_HOSTS" in workflow
    assert "~/.ssh/known_hosts" in workflow


def test_deployment_does_not_echo_environment_secret():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    assert "echo $STAGING_ENV_FILE" not in workflow
    assert "printf '%s\\n' \"$STAGING_ENV_FILE\"" in workflow


def test_rollback_is_present_and_no_google_action_is_introduced():
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text().lower()
    assert "rollback-staging:" in workflow
    assert "googleapis.com" not in workflow
    assert "google.com" not in workflow
