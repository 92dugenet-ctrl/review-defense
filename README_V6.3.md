# Review Defense V6.3 — Production Frontend & Operations Console

V6.3 adds the operational console on top of the V6.x API.

## Implemented
- Same-origin static operations console at `/app` and `/app/`.
- Responsive dark operations UI with dashboard, reviews, cases, evidence, approvals, submissions, alerts, audit and organization views.
- Bearer-session login against `/v1/auth/login`.
- Automatic session expiry handling and logout.
- Role/tenant context displayed from `/v1/me`; no tenant can be selected by the browser.
- Server-side RBAC remains authoritative; frontend controls are presentation only.
- Live API data for reviews, cases, evidence, approvals, submissions and organization members.
- Search/filter for tabular operational data.
- No Google credentials, OAuth secrets or API keys in frontend assets.
- No direct Google API calls from the browser.
- Submission view exposes only the server-provided external-call state; the console cannot invoke Google directly.
- Static file root confinement prevents traversal outside the frontend directory.
- Existing V4.1–V6.2 test suite preserved.

## Architecture
Browser -> same-origin `/app` -> `/v1/*` API -> identity/RBAC -> application repositories/vault/jobs.

The frontend is intentionally thin: security, authorization, validation, state transitions and Google actions remain server-side.

## Validation
**177 tests pass** with `pytest -q`.
