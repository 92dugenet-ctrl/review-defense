# V6.40 UAT campaign closure

The campaign is closed only when every scenario has PASS, an accepted documented BLOCKED state, or an explicitly linked defect awaiting the next campaign. No missing row is treated as PASS.

Closure record must include:
- campaign start/end;
- commit SHA;
- CI run;
- staging URL (if live);
- executed scenario count;
- PASS/FAIL/BLOCKED counts;
- open defects;
- security exceptions;
- human-gate verification;
- external-action verification;
- final GO/HOLD state.
