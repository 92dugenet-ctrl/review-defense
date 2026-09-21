# Review Defense — V6.34

## GitHub-controlled staging deployment

V6.34 adds a production-shaped GitHub Actions deployment path for an external HTTPS staging host. The workflow builds and transfers the exact repository release over pinned SSH host keys, writes the staging environment without printing secrets, starts PostgreSQL + migrations + the application + Caddy with Docker Compose, runs live HTTPS certification, and provides a bounded rollback job using the previous release.

### Required GitHub Environment `staging` secrets

- `STAGING_SSH_HOST`
- `STAGING_SSH_USER`
- `STAGING_SSH_PRIVATE_KEY`
- `STAGING_SSH_KNOWN_HOSTS`
- `STAGING_ENV_FILE` — complete staging `.env`; never commit it
- `STAGING_BASE_URL` — HTTPS URL
- optional `STAGING_SSH_PORT`

The workflow does not require a GitHub-hosted production credential and never invokes Google APIs. Live certification remains bounded to `/health`, `/ready`, security headers and protected `/metrics`.

### Deployment model

`main` push → regression/release gates → SSH deployment → Docker Compose → migrations → live HTTPS certification. A failed deployment triggers a rollback job that restores the previous release directory.

The actual staging host, DNS, PostgreSQL instance and TLS certificate are still external infrastructure. V6.34 provides the automation but does not claim that infrastructure has been provisioned.
