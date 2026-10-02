# Review Defense V6.40 — UAT deterministic test data

This specification defines the disposable UAT dataset used by the V6.40 campaign. It is synthetic, tenant-isolated and must never target production.

## Tenants
- Tenant A: Alpha
- Tenant B: Beta
- Roles per tenant: OWNER, ADMIN, ANALYST, CLIENT, VIEWER
- Three reviews per tenant: positive, critical, neutral
- Three dossiers per tenant: OPEN, FROZEN, APPROVED
- Evidence, facts, contradiction finding, checklist, alert, decision, snapshot, approval and prepared submission are synthetic.

## Safety
- Only `REVIEW_DEFENSE_TEST_DATABASE_URL` may be used.
- `DATABASE_URL` is explicitly rejected as a test target.
- External actions are disabled.
- All test objects are disposable.

## Required assertions
1. Tenant A cannot read or mutate Tenant B data.
2. Review → case creation is available to authorized roles.
3. Decision → freeze → human approval → controlled preparation is enforced.
4. Submission preparation has `external_call=false`.
5. Idempotency is stable across repeated requests.

The executable seed is `scripts/sandbox_seed.py`; the UAT certification contract is `scripts/uat_v640_certification.py`.
