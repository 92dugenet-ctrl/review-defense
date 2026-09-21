#!/usr/bin/env python3
"""V6.40 GitHub-hosted staging contract validation.

This does not deploy anything and does not require SSH credentials. It verifies
that GitHub Actions can run release/staging validation safely and that the
configured eCloudServ webhook is the deployment boundary.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.40"

REQUIRED = [
    ".github/workflows/review-defense-staging.yml",
    "docker-compose.staging.yml",
    "Dockerfile",
    "Caddyfile",
    "scripts/staging_certification.py",
    "scripts/postgres_certification.py",
    "scripts/staging_check.py",
    "scripts/browser_e2e.py",
    "scripts/dr_validate.py",
    "scripts/release_check.py",
    "scripts/deploy_staging.py",
]


def checks() -> dict[str, bool]:
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    compose = (ROOT / "docker-compose.staging.yml").read_text()
    return {
        "version": VERSION == "6.40",
        "workflow_present": (ROOT / REQUIRED[0]).is_file(),
        "required_artifacts": all((ROOT / p).is_file() for p in REQUIRED),
        "workflow_read_only_permissions": "contents: read" in workflow,
        "workflow_runs_regression": "pytest -q" in workflow,
        "workflow_runs_release_check": "python scripts/release_check.py" in workflow,
        "workflow_runs_staging_contract": "python scripts/staging_certification.py" in workflow,
        "postgres_integration_job": "postgres-integration:" in workflow and "postgres:16-alpine" in workflow and "REVIEW_DEFENSE_TEST_DATABASE_URL" in workflow,
        "postgres_certification": "python scripts/postgres_certification.py" in workflow,
        "workflow_live_certification_is_manual": "workflow_dispatch:" in workflow and "inputs:" in workflow,
        "ecloudserv_webhook_staging": "ecloudserv-staging:" in workflow and "Verify eCloudServ webhook deployment" in workflow,
        "no_ssh_staging_deployment": "STAGING_SSH_" not in workflow and "ssh -i" not in workflow and "scp -i" not in workflow,
        "no_ssh_rollback": "rollback-staging:" not in workflow,
        "no_staging_environment_dependency": "environment: staging" not in workflow,
        "postgres_healthcheck": "pg_isready" in compose,
        "migrations_before_app": "python scripts/migrate.py" in compose,
        "no_google_actions": "google" not in workflow.lower().replace("review-defense", ""),
    }


def main() -> int:
    result = checks()
    result["all"] = all(result.values())
    report = {"version": VERSION, "status": "PASS" if result["all"] else "FAIL", "checks": result}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if result["all"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
