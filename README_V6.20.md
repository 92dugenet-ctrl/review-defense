# Review Defense V6.20 — Production Foundation

V6.20 turns the V6.19 application into a production-oriented deployment baseline without changing the human-gated review workflow.

## Implemented
- Environment-backed production configuration and startup validation.
- Production requires `DATABASE_URL` and a non-loopback bind address.
- Deterministic numbered PostgreSQL migration runner with `schema_migrations` bookkeeping.
- Migration `018_v620_production_foundation.sql` adds tenant-scoped runtime settings with RLS.
- PostgreSQL `ping()` health primitive.
- `/health` reports V6.20 and remains a lightweight liveness endpoint.
- `/ready` checks the database when a repository is configured and returns `503` when dependencies are not ready.
- Baseline security response headers, including HSTS in production.
- Gunicorn WSGI entrypoint, Dockerfile, Docker Compose PostgreSQL/app stack, `.env.example`, and migration CLI.
- Regression tests for configuration, migrations, readiness, and production HTTP behavior.

## Security invariants preserved
- Tenant isolation and server-side RBAC remain enforced.
- No Google deletion, reporting, reply, or other external mutation is introduced.
- Decision → freeze → approval → submission gates remain unchanged.
- Evidence SHA-256 integrity is unchanged.
- Migration 018 uses tenant RLS for organization runtime settings.

## Operational usage
1. Copy `.env.example` to `.env` and replace credentials.
2. Start PostgreSQL and the application with `docker compose up --build`.
3. The container runs the migrations before starting Gunicorn.
4. Use `/health` for liveness and `/ready` for readiness.

## Limitation
V6.20 does not yet provide managed cloud infrastructure, automated backups, TLS termination/certificates, external log shipping, or a real production PostgreSQL integration test environment. Those remain pre-release work rather than being falsely treated as complete.
