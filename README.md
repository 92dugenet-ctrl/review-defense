# Review Defense

Review Defense is organized as a modular application with separate public frontend, authenticated application, backend domain services, database, administration, tests, and documentation.

## Architecture

- `frontend/public`: public marketing pages, reusable public components, assets, and styles.
- `frontend/auth`: login and registration experiences.
- `frontend/application`: authenticated customer workspace, grouped by product capability.
- `backend`: API and domain modules. Existing Python implementation currently lives in `src/`, with the WSGI/application entrypoints at the repository root; migration into these domain boundaries must preserve imports and runtime behavior.
- `database`: schema, migrations, and database policies. Existing SQL migrations currently live in `migrations/`.
- `admin`: internal administration and monitoring.
- `tests`: unit, integration, security, and end-to-end coverage.
- `docs`: technical, legal, security, and API documentation.

## Migration rules

1. Preserve working behavior and public/API contracts while relocating code.
2. Do not merge source branches wholesale. Select compatible changes by file and feature, resolving overlaps against the current `develop` baseline.
3. Keep organization/tenant isolation, authorization checks, auditability, evidence integrity, and human approval gates intact.
4. Keep raw evidence and source records immutable; distinguish observed, estimated, derived, and unknown values.
5. Do not introduce automatic Google review responses, removals, or reporting actions.
6. Keep secrets out of the repository. Use environment configuration and the existing deployment workflows.
7. Run unit, integration, security, migration, frontend build, and end-to-end checks before declaring a migration complete.

## Current migration status

This commit establishes the target directory boundaries without deleting or moving legacy modules. Existing paths remain authoritative until each module has been migrated and its imports, routes, workflows, and tests have been verified.
