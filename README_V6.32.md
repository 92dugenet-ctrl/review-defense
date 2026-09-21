# Review Defense V6.32 — Production Deployment Verification & Live Staging Certification

V6.32 adds a bounded staging certification layer on top of the V6.31 release-candidate gate.

## Certification checks
- staging Docker Compose contains PostgreSQL health gating and runs migrations before Gunicorn;
- HTTPS/TLS is enforced by the Caddy staging contract;
- production-mode security headers remain enabled;
- public base URL and MFA encryption key are mandatory staging settings;
- frontend remains free of direct Google endpoints and secrets;
- live certification, when `STAGING_BASE_URL` is supplied, verifies `/health`, `/ready`, required security headers and that unauthenticated `/metrics` is not exposed;
- without `STAGING_BASE_URL`, the script reports `CONTRACT-PASS-NOT-LIVE-CERTIFIED` and never claims that live infrastructure was tested.

## Run

Repository contract only:
```bash
python scripts/staging_certification.py
```

Live staging certification:
```bash
STAGING_BASE_URL=https://staging.example.com python scripts/staging_certification.py --live
```

The live command is read-only. It does not deploy, migrate, restore, submit Google actions, or modify production data.

## Limitations
A repository contract pass is not a live staging certification. Live certification requires an actual HTTPS staging environment and `STAGING_BASE_URL`. Browser E2E and real PostgreSQL DR remain separate bounded checks and must be executed against non-production infrastructure.
