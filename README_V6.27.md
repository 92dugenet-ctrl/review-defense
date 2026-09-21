# Review Defense V6.27 — Production Deployment & Staging Hardening

## Delivered
- Production deployment contract with explicit HTTPS public URL and trusted reverse-proxy opt-in.
- Strong browser security headers including CSP, Permissions-Policy, COOP, CORP, HSTS, frame and content protections.
- Caddy TLS reverse-proxy deployment for staging/production-like environments.
- Dedicated `docker-compose.staging.yml` with PostgreSQL, application and TLS proxy.
- Bounded non-destructive staging smoke checker (`scripts/staging_check.py`).
- Health endpoint versioned to V6.27 and readiness remains database-aware.

## Security
- Production refuses to start without HTTPS public URL.
- Production refuses to start without explicit `TRUST_PROXY=true` when the deployment trusts proxy semantics.
- No external Google action is introduced.
- Human approval gates remain unchanged.

## Known limitation
A real staging deployment and browser-level E2E run require an externally reachable HTTPS domain, DNS, TLS issuance and a real PostgreSQL service. This environment does not provide those external infrastructure prerequisites, so the code/configuration is validated locally but no claim of a live staging deployment is made.
