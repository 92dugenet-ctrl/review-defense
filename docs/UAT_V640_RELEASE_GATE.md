# V6.40 Release Gate / sign-off

## Mandatory gates
- [ ] Python regression suite green
- [ ] release static contract green
- [ ] PostgreSQL migrations idempotent
- [ ] forced RLS/tenant isolation verified
- [ ] sandbox seed/certification green
- [ ] 47 UAT scenarios executed
- [ ] no BLOCKER defects open
- [ ] browser E2E green on live staging
- [ ] MFA flow green when enabled
- [ ] human approval gate verified
- Human approval is mandatory before any external submission.
- [ ] external Google action remains disabled

## Decision states
- **HOLD_STEP_3** — one or more mandatory gates are not certified.
- **GO_STEP_4** — all mandatory gates have concrete evidence.

Repository-only checks must never be labelled live staging certification.
