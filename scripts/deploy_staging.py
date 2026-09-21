#!/usr/bin/env python3
"""V6.40 deterministic eCloudServ staging deployment preflight.

This module validates the GitHub Actions/eCloudServ webhook deployment
contract. It never contacts a remote host, uses SSH, or executes a deployment.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.40"

REQUIRED_FILES = [
    ".github/workflows/review-defense-staging.yml",
    "docker-compose.staging.yml",
    "Dockerfile",
    "Caddyfile",
    "scripts/staging_certification.py",
]


def workflow_checks() -> dict[str, bool]:
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    return {
        "version": VERSION in workflow,
        "required_files": all((ROOT / p).is_file() for p in REQUIRED_FILES),
        "no_ssh_deployment": "STAGING_SSH_" not in workflow and "ssh -i" not in workflow and "scp -i" not in workflow,
        "no_ssh_rollback": "rollback-staging:" not in workflow,
        "ecloudserv_webhook": "ecloudserv-staging:" in workflow and "Verify eCloudServ webhook deployment" in workflow,
        "manual_dispatch": "workflow_dispatch:" in workflow,
        "push_main_deploy": "branches: [main]" in workflow,
        "live_base_url_optional": "No STAGING_BASE_URL configured" in workflow,
        "post_deploy_certification": "scripts/staging_certification.py --live" in workflow,
        "no_google_actions": "googleapis.com" not in workflow.lower() and "google.com" not in workflow.lower(),
        "read_only_permissions": "contents: read" in workflow,
    }


def validate_configuration() -> dict[str, bool]:
    # STAGING_BASE_URL is only needed for optional live verification; the
    # eCloudServ deployment itself is triggered by the GitHub push webhook.
    base_url = os.environ.get("STAGING_BASE_URL", "").strip()
    return {
        "staging_base_url_optional": not base_url or base_url.startswith("https://"),
    }


def main() -> int:
    checks = workflow_checks()
    configuration = validate_configuration()
    report = {
        "version": VERSION,
        "status": "PASS" if all(checks.values()) and all(configuration.values()) else "FAIL",
        "checks": checks,
        "configuration": configuration,
        "note": "eCloudServ deployment is triggered by the repository push webhook; no SSH credentials are required.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
