# Review Defense V6.26 — Production Frontend

V6.26 turns the existing static operations console into a production-oriented frontend for the authenticated Review Defense workflow.

## Delivered
- Responsive same-origin console with dashboard, reviews, cases, SLA workload, escalations, evidence, approvals, submissions, alerts and organization views.
- Login with organization ID, password and conditional MFA code.
- Recovery request, reset-password and email-verification routes on the same origin.
- Case Workspace enriched with readiness, claims, policy signals, evidence, evidence matrix and decision lifecycle.
- Explicit human-gated actions: create decision, freeze, approve and prepare submission.
- No frontend call to Google or any external review action endpoint.
- Change-password and MFA enrollment entry points in organization settings.
- Client-side rendering uses HTML escaping for API-provided values and never embeds server secrets.
- Same-origin API calls only; Bearer session token is kept in localStorage for this reference deployment.

## Security invariants
- Tenant is selected only during authentication; subsequent API calls use the authenticated session.
- The frontend does not bypass server-side RBAC or approval gates.
- Preparing a submission does not execute an external call.
- Evidence SHA-256 values are displayed as server-provided integrity metadata.
- Contradictions/evidence remain human-review workflows.

## Known production hardening remaining
- Prefer an HttpOnly/Secure/SameSite cookie session for a public deployment instead of localStorage bearer storage.
- Add CSP as an HTTP response header at the reverse proxy/application boundary.
- Run browser-level E2E tests against a real staging deployment.
- Wire a real PostgreSQL-backed staging environment and validate the complete authentication/frontend flow.
