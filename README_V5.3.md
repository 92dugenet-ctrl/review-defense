# Review Defense V5.3 — End-to-End Testing

V5.3 adds a real framework-neutral end-to-end harness spanning the application
contracts introduced in V4.4 through V5.2.

## Covered flow

`review ingestion → claim extraction → policy signals → evidence vault → case/dossier → freeze → human approval → submission preparation → explicit submission recording → observed outcome`

The harness deliberately does **not** call Google or any external network.
External submission is represented by an explicit boundary: an approved
submission can be *recorded* with an external reference, but no external call
is made by the test harness.

## Regression coverage

The V5.3 suite keeps the complete V4.1–V5.2 regression suite and adds E2E
scenarios for:

- pipeline happy path;
- duplicate review/idempotency guard;
- cross-tenant isolation;
- malformed review input;
- legitimate negative reviews / false-positive guard;
- allegations requiring evidence and human review;
- evidence integrity and corrupted content;
- invalid upload handling;
- dossier modification invalidating approval;
- role-based approval controls;
- submission gating and explicit external boundary;
- observed outcomes without inferred reasons;
- signed download tenant binding and expiry;
- expired sessions;
- immutable dossier snapshots.

## Production boundary

This is an application/integration test harness, not a live Google connector.
Production still requires real deployment controls from V5.0–V5.2, including
secret management, TLS, private object storage, encryption/KMS, malware
scanning, PostgreSQL backups/migrations/pooling, monitoring and least-privilege
credentials.
