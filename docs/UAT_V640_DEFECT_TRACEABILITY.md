# V6.40 UAT defect traceability

Use one row per defect. Never silently convert a failed scenario into a pass.

| Field | Required value |
|---|---|
| Defect ID | UAT-YYYYMMDD-NNN |
| Scenario | UAT scenario ID |
| Severity | BLOCKER / HIGH / MEDIUM / LOW |
| Tenant | A / B |
| Role | actor role |
| Expected | acceptance criterion |
| Actual | observed result |
| Evidence | artifact/log/screenshot reference |
| Reproducible | YES / NO |
| Fix commit | Git SHA |
| Retest | PASS / FAIL / BLOCKED |
| Closure | owner + date |

A BLOCKER prevents a GO decision. A defect is closed only after the same scenario is rerun successfully.
