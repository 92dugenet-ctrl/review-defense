"""V6.40 release static validation.

This check is deterministic and non-destructive. It validates the artifacts that
must be present before a live browser E2E run is considered meaningful.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required = [
        "frontend/index.html", "frontend/assets/app.js", "frontend/assets/app.css",
        "Dockerfile", "docker-compose.yml", "docker-compose.staging.yml", "Caddyfile",
        "wsgi.py", "src/api_server.py", "src/deployment.py", "scripts/staging_check.py",
        "scripts/browser_e2e.py", "scripts/dr_validate.py", "scripts/release_candidate_gate.py", "scripts/staging_certification.py", "scripts/staging_e2e.py", "scripts/github_staging_contract.py", "scripts/deploy_staging.py", "scripts/postgres_certification.py", "scripts/sandbox_seed.py", "scripts/sandbox_certification.py", "scripts/uat_v640_certification.py", "scripts/uat_environment_readiness.py",
    ]
    missing = [p for p in required if not (ROOT / p).is_file()]
    if missing:
        raise SystemExit(f"missing release artifacts: {missing}")

    js = (ROOT / "frontend/assets/app.js").read_text()
    html = (ROOT / "frontend/index.html").read_text()
    forbidden = ["googleapis.com", "google.com", "SMTP_PASSWORD", "DATABASE_URL", "OPENAI_API_KEY"]
    blob = "\n".join([js, html])
    hits = [x for x in forbidden if x in blob]
    if hits:
        raise SystemExit(f"forbidden frontend material: {hits}")

    required_routes = [
        "/v1/auth/login", "/v1/auth/recovery/request", "/v1/auth/recovery/reset",
        "/v1/auth/email-verification/verify", "/v1/auth/mfa/confirm",
        "/v1/cases/", "/evidence-matrix", "/review-readiness", "/decision",
        "/freeze", "/approve", "/submit",
    ]
    missing_routes = [r for r in required_routes if r not in js]
    if missing_routes:
        raise SystemExit(f"frontend route contracts missing: {missing_routes}")

    if "confirm('Figer le dossier" not in js or "confirm('Confirmer l’approbation humaine" not in js:
        raise SystemExit("human approval gate not present in frontend")
    if "Aucune action externe ne sera exécutée" not in js:
        raise SystemExit("external action safety notice missing")

    csp = (ROOT / "src/deployment.py").read_text()
    for token in ["object-src 'none'", "frame-ancestors 'none'", "connect-src 'self'"]:
        if token not in csp:
            raise SystemExit(f"security header contract missing: {token}")

    print("release check: PASS")
    print(f"required_artifacts={len(required)}")
    print(f"frontend_route_contracts={len(required_routes)}")
    print("security_contract=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
