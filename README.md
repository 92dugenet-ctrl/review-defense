# Review Defense — V6.40

Review Defense is a multi-tenant platform for analysing online reviews, structuring evidence, managing cases and preparing controlled review-platform submissions.

## V6.40 status

- Automated regression suite: 416 passed, 2 skipped in the latest successful CI run.
- PostgreSQL migrations, health checks and tenant isolation are covered by CI.
- Demonstration sandbox covers two isolated organisations and the core case/evidence/approval flow.
- Human approval is required before a submission can proceed.
- The application does not automatically delete, report or answer Google reviews.
- eCloudServ deployment is triggered through the repository push webhook.
- Live staging and browser E2E certification remain environment-dependent and are not claimed by repository-only tests.

## Main areas

- `frontend/` — public and application UI.
- `src/` — application services, API, identity, evidence, cases, Google read/sync integration and SEO.
- `migrations/` — PostgreSQL schema migrations.
- `scripts/` — migration, staging, sandbox, release and certification tooling.
- `tests/` — regression and versioned contract tests.

## Safety boundary

The product follows:

**Decision → Freeze → Human Approval → Controlled Preparation/Submission**

No automated Google deletion, reporting or response is performed by the application.

## Deployment

The repository is the source of truth for application code. External infrastructure configuration (database credentials, deployment provider settings, DNS/TLS and live staging credentials) is intentionally kept outside the repository.

