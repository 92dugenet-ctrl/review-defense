# Review Defense V6.36 — HTTPS + Authentication/MFA + Real Staging E2E

V6.36 extends the GitHub-native staging pipeline from deployment to a real HTTPS certification path.

## Added
- dedicated live staging E2E runner (`scripts/staging_e2e.py`);
- HTTPS-only enforcement for live certification;
- dedicated staging authentication credentials supplied through GitHub Environment secrets;
- optional required MFA certification using an existing dedicated MFA-enabled staging account;
- password-only MFA bypass test must fail before a TOTP login is accepted;
- real Chromium browser validation against `/app`;
- browser resource inspection rejects direct Google/Google APIs calls;
- GitHub Actions `staging-e2e` job runs only after successful deployment;
- Playwright Chromium installed in CI;
- release contract includes the new certification script.

## Required GitHub `staging` environment secrets
- `STAGING_SSH_HOST`
- `STAGING_SSH_USER`
- `STAGING_SSH_PRIVATE_KEY`
- `STAGING_SSH_KNOWN_HOSTS`
- `STAGING_ENV_FILE`
- `STAGING_BASE_URL` (must be HTTPS)
- `E2E_EMAIL`
- `E2E_PASSWORD`
- `E2E_ORGANIZATION_ID`
- `E2E_MFA_SECRET` when the dedicated account has MFA enabled.

The E2E account must be dedicated to staging. The workflow does not disable MFA, alter Google data, report reviews, delete reviews, or submit external actions.

## Certification states
Without live secrets, repository tests remain contract-only. A live staging run is certified only after HTTPS health/readiness, protected metrics, authentication, MFA enforcement when configured, browser rendering and no-direct-Google-resource checks pass.

## Safety
- Human approval gates remain unchanged.
- No autonomous Google deletion/report/reply/submission is introduced.
- Tenant isolation/RLS and evidence integrity remain required.
