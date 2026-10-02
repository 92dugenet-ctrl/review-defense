# V6.40 final report / manifest

## Campaign manifest

This manifest is the final packaging layer for the UAT campaign. It does not declare a campaign PASS by itself.

### Required inputs
- 47-scenario result CSV
- final checklist
- defect traceability
- PostgreSQL certification
- sandbox certification
- live staging certification, when configured
- live browser E2E report, when configured
- environment readiness record
- commit SHA and CI run identifier

### Output
The final report must contain:
- executed scenario count;
- PASS / FAIL / BLOCKED counts;
- open defects and severities;
- evidence references;
- environment and commit identifiers;
- human-gate verification;
- external-action verification;
- final state: GO_STEP_4 or HOLD_STEP_3.

### Manifest rule
An absent artifact is not a PASS. Live infrastructure checks cannot be inferred from repository-only checks.
