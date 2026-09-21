#!/usr/bin/env python3
"""V6.40 deterministic staging deployment preflight.

This module validates the environment used by the GitHub Actions deployment
workflow. It never contacts a remote host and never executes a deployment.
"""
from __future__ import annotations

import json
import os
import re
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

SECRET_NAMES = [
    "STAGING_SSH_HOST",
    "STAGING_SSH_USER",
    "STAGING_SSH_PRIVATE_KEY",
    "STAGING_SSH_KNOWN_HOSTS",
    "STAGING_ENV_FILE",
    "STAGING_BASE_URL",
]


def workflow_checks() -> dict[str, bool]:
    workflow = (ROOT / ".github/workflows/review-defense-staging.yml").read_text()
    return {
        "version": VERSION in workflow,
        "required_files": all((ROOT / p).is_file() for p in REQUIRED_FILES),
        "staging_environment": "environment: staging" in workflow,
        "manual_dispatch": "workflow_dispatch:" in workflow,
        "push_main_deploy": "branches: [main]" in workflow,
        "ssh_deploy": "ssh" in workflow and "STAGING_SSH_PRIVATE_KEY" in workflow,
        "known_hosts_pinned": "STAGING_SSH_KNOWN_HOSTS" in workflow and "known_hosts" in workflow,
        "env_not_logged": "set -x" not in workflow and "STAGING_ENV_FILE" in workflow,
        "post_deploy_certification": "scripts/staging_certification.py --live" in workflow,
        "rollback_support": "docker compose" in workflow and "staging_previous" in workflow,
        "no_google_actions": "googleapis.com" not in workflow.lower() and "google.com" not in workflow.lower(),
        "read_only_permissions": "contents: read" in workflow,
    }


def validate_secret_names() -> dict[str, bool]:
    # This only validates naming/documentation; secrets themselves must never be printed.
    env = os.environ
    return {name: bool(env.get(name, "").strip()) for name in SECRET_NAMES}


def main() -> int:
    checks = workflow_checks()
    report = {
        "version": VERSION,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "secret_presence": {k: bool(v) for k, v in validate_secret_names().items()},
        "note": "Secret values are never emitted by this validator.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
