# Review Defense V6.28 — E2E Browser & Release Validation

## Delivered
- Real Chromium browser E2E runner using Playwright.
- Local browser E2E path covering login, dashboard, case view and review view.
- Browser resource inspection ensuring no direct Google endpoint is contacted by the frontend.
- Deterministic release-candidate artifact/route/security validation script.
- Optional browser test in the regression suite, gated by `RUN_BROWSER_E2E=1`.
- E2E runner is non-destructive and does not execute external submission actions.

## Release safety
- Browser tests do not call Google APIs.
- No automated review deletion/reporting/reply is introduced.
- Human approval gates remain explicit in the UI and server.
- Release check rejects credentials/secrets and external Google URLs embedded in frontend artifacts.

## How to run

```bash
python scripts/release_check.py
E2E_EMAIL='...' E2E_PASSWORD='...' E2E_ORGANIZATION_ID='...' E2E_BASE_URL='https://staging.example' python scripts/browser_e2e.py
RUN_BROWSER_E2E=1 pytest -q tests/test_v628_release_e2e.py
```

A real staging E2E run still requires an externally reachable staging URL, PostgreSQL, valid identity data and TLS. No live staging deployment is claimed by this release.
