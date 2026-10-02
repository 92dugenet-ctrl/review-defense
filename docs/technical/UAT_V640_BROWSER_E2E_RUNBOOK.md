# V6.40 Browser E2E runbook

## Preconditions
- HTTPS `STAGING_BASE_URL`
- dedicated E2E account
- `E2E_EMAIL`, `E2E_PASSWORD`, `E2E_ORGANIZATION_ID`
- `E2E_MFA_SECRET` when MFA is enabled
- Chromium/Playwright available in CI

## Flow
1. Open `/app`.
2. Verify login form is rendered before interacting with it.
3. Login with organization ID.
4. Complete MFA when required.
5. Verify dashboard.
6. Open Reviews and verify review cards.
7. Use **Créer le dossier** on a synthetic review.
8. Verify the new dossier is visible.
9. Open the case and verify the human-gated actions.
10. Verify no request/resource targets Google directly.

## Failure diagnostics
The runner must capture URL, title, readyState, body text, app root HTML, script sources, asset responses, page errors and console messages when the login selector is absent. This avoids masking deployment/cache failures as authentication failures.

Implementation: `scripts/staging_e2e.py` and `scripts/browser_e2e.py`.
