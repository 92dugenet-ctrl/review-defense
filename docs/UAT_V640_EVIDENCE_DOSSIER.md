# V6.40 UAT evidence dossier

The dossier is the single evidence manifest for the campaign. It references, rather than embeds, large logs/traces.

Required sections:
1. build commit;
2. CI jobs;
3. PostgreSQL certification;
4. sandbox certification;
5. 47-scenario result CSV;
6. browser E2E report;
7. defects and retests;
8. security/human-gate evidence;
9. environment readiness;
10. final sign-off.

Secrets, passwords, MFA seeds and database DSNs must never be stored in this dossier.
