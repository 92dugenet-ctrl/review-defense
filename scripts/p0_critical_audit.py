"""P0 critical-path audit for Review Defense.

Static, deterministic, non-destructive checks for the six runtime-critical
blocks: API, PostgreSQL isolation, business approval chain, security, frontend,
and deployment/runtime contracts.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"P0 FAIL: missing required file: {path}")
    return p.read_text(encoding="utf-8")


def require(blob: str, needle: str, label: str) -> None:
    if needle not in blob:
        raise SystemExit(f"P0 FAIL: {label}: missing {needle!r}")


def main() -> int:
    api = read("src/api_server.py")
    postgres = read("src/postgres_repository.py") + read("src/postgres_api_repository.py")
    identity = read("src/identity.py")
    security = read("src/security_hardening.py")
    mfa = read("src/mfa.py")
    decision = read("src/case_decision_service.py")
    submission = read("src/case_submission_service.py")
    frontend = read("frontend/assets/app.js")
    html = read("frontend/index.html")
    deployment = read("src/deployment.py")
    wsgi = read("wsgi.py")

    # P0-1 API/backend boundary.
    require(api, "class Application", "API application boundary")
    require(api, "def _authenticate", "API authentication boundary")
    require(api, "def _json", "API JSON response boundary")
    require(api, "RateLimiter", "API rate limiting")
    require(api, "organization_id", "API tenant context")
    if "raise APIError" not in api:
        raise SystemExit("P0 FAIL: API error handling contract missing")

    # P0-2 PostgreSQL persistence + tenant isolation.
    require(postgres, "def transaction(self, organization_id", "PostgreSQL tenant transaction")
    require(postgres, "set_config('app.organization_id', %s, true)", "PostgreSQL tenant context")
    require(postgres, "def transaction_without_tenant", "explicit non-tenant transaction boundary")
    require(postgres, "NOBYPASSRLS", "non-bypass-RLS integration contract")
    if "organization_id" not in postgres:
        raise SystemExit("P0 FAIL: repository has no organization_id boundary")

    # P0-3 business chain: Decision -> Freeze -> Approval -> Submission.
    require(decision, "def freeze(", "decision freeze operation")
    require(decision, "request_approval(", "freeze must transition to approval")
    require(decision, "def approve(", "human approval operation")
    require(decision, 'case.status = "READY_TO_SUBMIT"', "approval readiness transition")
    require(submission, 'decision.status != "APPROVED"', "submission approval guard")
    require(submission, "explicit human approval required before submission", "submission human gate")

    # P0-4 authentication/security.
    require(identity, "generate_session_token()", "session token issuance")
    require(identity, "validate_role", "role validation")
    require(security, "hmac.compare_digest", "constant-time token/password comparison")
    require(security, "PBKDF2_ITERATIONS = 310_000", "password hashing policy")
    require(security, "def require_tenant", "tenant authorization boundary")
    require(mfa, "def verify_totp", "MFA verification")
    require(mfa, "hmac.compare_digest", "constant-time MFA comparison")

    # P0-5 frontend boot/auth/application contract.
    require(frontend, "window.boot", "frontend boot export")
    require(frontend, "/v1/auth/login", "frontend login contract")
    require(frontend, "/v1/me", "frontend authenticated-session contract")
    for route in ("/v1/cases/", "/evidence-matrix", "/review-readiness", "/decision", "/freeze", "/approve", "/submit"):
        require(frontend, route, f"frontend business route {route}")
    require(frontend, "Confirmer l’approbation humaine", "frontend human approval confirmation")
    require(frontend, "Aucune action externe ne sera exécutée", "frontend external-action safety notice")
    require(html, "app.js", "frontend script loading")

    # P0-6 deployment/runtime.
    require(deployment, "object-src 'none'", "CSP object-src")
    require(deployment, "frame-ancestors 'none'", "CSP frame-ancestors")
    require(deployment, "connect-src 'self'", "CSP connect-src")
    require(wsgi, "application", "WSGI application export")
    for path in ("Dockerfile", "docker-compose.yml", "Caddyfile"):
        read(path)

    print("P0 AUDIT: PASS")
    print("p0_api=PASS")
    print("p0_postgresql_tenant_isolation=PASS")
    print("p0_business_approval_chain=PASS")
    print("p0_auth_security=PASS")
    print("p0_frontend=PASS")
    print("p0_deployment=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
