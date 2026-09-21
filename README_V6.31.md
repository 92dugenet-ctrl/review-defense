# Review Defense V6.32 — Release Candidate / Production Readiness Gate

V6.32 turns the accumulated V6.x controls into a deterministic release gate.

## Gate checks
- application health version is V6.32;
- release artifacts, staging smoke test and browser E2E are present;
- production security-header contracts remain present;
- frontend retains explicit human freeze/approval gates;
- frontend contains no direct Google endpoint or credential material;
- disaster recovery requires the dedicated `REVIEW_DEFENSE_TEST_DATABASE_URL`, a separate restore target and `--confirm`;
- the full regression suite is executed;
- Python sources/tests compile successfully;
- the existing static release contract passes;
- an auditable JSON report is written to `artifacts/v6.32-release-candidate.json`.

## Run

```bash
python scripts/release_candidate_gate.py
```

For contract-only validation:

```bash
python scripts/release_candidate_gate.py --skip-tests
```

`--skip-tests` intentionally cannot produce a release `PASS`.

## Safety

The gate is non-destructive. It does not deploy, run production migrations, restore a production database, contact Google, delete/report/reply to reviews, or perform autonomous remediation. A real PostgreSQL DR cycle remains dependent on dedicated non-production staging databases as documented in V6.30.

## Release interpretation

`PASS` means the repository-level release gate passed in the execution environment. It does not mean that a live production deployment, live PostgreSQL DR restore, TLS certificate issuance, or external monitoring service has been exercised here.
