# V6.40 UAT execution protocol

## Order
1. Verify test database isolation.
2. Apply migrations twice and require the second pass to be a no-op.
3. Seed Tenant A/B with `scripts/sandbox_seed.py`.
4. Execute the 47 cases in `UAT_V640_TEST_CASES.csv`.
5. Record every failure with scenario ID, timestamp, tenant, actor role, request, expected result, actual result and evidence reference.
6. Run browser E2E only after API/database certification is green.
7. Produce the final execution record and handoff.

## Stop conditions
- Production database is detected.
- Cross-tenant data becomes visible.
- Human approval gate can be bypassed.
- Any external Google action is observed.
- A test account cannot be uniquely identified.

## Evidence rule
A green static/CI result is not a substitute for live staging certification. Live certification requires the configured staging URL and E2E secrets.
