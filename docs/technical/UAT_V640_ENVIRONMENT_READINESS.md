# V6.40 environment readiness

## Repository
- workflow present
- Docker/staging contract present
- migrations present
- browser runners present
- deterministic test-data contract present

## Runtime prerequisites
- PostgreSQL test database separate from production
- eCloudServ webhook connected to `main`
- `STAGING_BASE_URL` points to the deployed V6.40 HTTPS endpoint
- E2E account secrets configured
- MFA secret configured when the account is MFA-enforced

## Important
A repository push can trigger eCloudServ deployment, but it does not prove that the server has deployed the new commit. Live health/readiness and browser E2E must be observed separately.
