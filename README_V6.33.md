# Review Defense V6.33 — GitHub-native Free Staging Bootstrap

V6.33 prepares a staging workflow that can be operated entirely from GitHub-hosted runners, without requiring the user to own a PC or run a local server.

## What is implemented

- GitHub Actions workflow for pull requests and `main` pushes.
- Full regression suite, Python compilation, release contract and staging contract executed in CI.
- Repository-only staging certification remains non-destructive and requires no production secrets.
- Optional manual live certification accepts an explicit `STAGING_BASE_URL` and requires HTTPS.
- GitHub Actions permissions are restricted to `contents: read`.
- Live certification is isolated behind `workflow_dispatch`; normal pushes cannot probe an arbitrary external host.
- Existing Docker/PostgreSQL/Caddy staging stack is retained.
- No Google API call, review deletion, reporting, reply, or other external Google action is introduced.

## GitHub workflow

The workflow is `.github/workflows/review-defense-staging.yml`.

Normal push/PR path:

```text
GitHub
  -> pytest
  -> compileall
  -> release_check
  -> GitHub staging contract
  -> repository staging certification
```

Optional live path:

```text
GitHub Actions (manual dispatch)
  -> STAGING_BASE_URL=https://...
  -> /health
  -> /ready
  -> security headers
  -> protected /metrics
```

The live job is read-only. It does not deploy, migrate, restore, or mutate production data.

## Important limitation

V6.33 does **not** claim that a public staging server has been provisioned. GitHub Actions provides the free CI execution layer; a persistent public staging URL still requires a cloud runtime/provider. Once such a URL exists, it can be certified through the manual workflow without a local PC.
