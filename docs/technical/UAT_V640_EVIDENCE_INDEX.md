# V6.40 evidence index

Each executed scenario must point to one or more immutable artifacts.

Recommended evidence classes:
- CI run URL / job log
- PostgreSQL certification JSON
- sandbox certification JSON
- browser E2E JSON
- screenshot or browser trace
- API request/response capture with secrets removed
- audit/event identifier
- defect record and retest result

Naming convention: `artifacts/uat/v6.40/<scenario-id>/<timestamp>-<kind>.<ext>`.
