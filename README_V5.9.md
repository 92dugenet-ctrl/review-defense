# Review Defense V5.9 — PostgreSQL Production Sync & Pub/Sub Receiver

V5.9 moves Google sync state and background-job enqueueing behind a PostgreSQL tenant-scoped persistence boundary.

## Implemented
- PostgreSQL tables for sync cursors, processed Pub/Sub events, normalized Google reviews and background jobs.
- Row-level security and `SET LOCAL app.organization_id` on every repository transaction.
- Atomic `claim_event_and_enqueue`: a duplicate Pub/Sub event cannot create a second job.
- PostgreSQL job enqueue idempotency with payload-fingerprint conflict detection.
- `FOR UPDATE SKIP LOCKED` tenant-scoped job claiming primitive.
- Authenticated Pub/Sub push receiver with injected verifier; unauthenticated pushes are rejected.
- Base64 Pub/Sub payload decoding and V5.8 review-event parser reuse.
- No Google mutation, deletion, reporting or reply is performed by this layer.

## Production boundary
The repository requires PostgreSQL and psycopg at deployment. The Pub/Sub verifier must be wired to Google's OIDC JWT validation (issuer, audience, signature and expiration) in the deployment environment. Tests use injected fakes and never call Google.
