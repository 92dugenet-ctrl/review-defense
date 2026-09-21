# Review Defense V5.8 — Google Sync Engine & Event Processing

V5.8 turns the V5.7 Google read adapter into a durable, event-driven synchronization layer.

## Implemented

- Durable SQLite sync state for per-tenant/account/location review cursors.
- Pub/Sub notification parser for `NEW_REVIEW` and `UPDATED_REVIEW` events.
- Event de-duplication by tenant + Google message ID.
- Notification-driven targeted `get_review` fetches.
- Notification fallback to location reconciliation when a review resource is not present.
- V5.6 background jobs for asynchronous Google sync work.
- Idempotent reconciliation jobs.
- Persisted pagination cursors and worker retries.
- Tenant isolation across event, cursor and result state.
- Safe resumption after process restart.
- Explicit mutation boundary remains intact: no reporting, deletion or replying.
- Tests use an injected fake transport; no live Google credentials/network are required.

## Google-specific design note

Google documents real-time Business Profile notifications through Cloud Pub/Sub, including new and updated review events. The current Notifications API is the supported notification configuration surface; the older v4 notification resource is deprecated. Google also documents an occasional inconsistency in review-list pagination after the first page. V5.8 therefore combines notification-driven targeted fetches with periodic reconciliation and never interprets a missing paginated review as deletion.

Sources:
- Google Business Profile notifications: https://developers.google.com/my-business/content/notification-setup
- Google review data: https://developers.google.com/my-business/content/review-data
- Google known pagination issue: https://developers.google.com/my-business/content/known-issues

## Production requirements

Configure Cloud Pub/Sub and the Google Notifications API in an approved Google Cloud project, grant the documented publishing permission, authenticate the subscriber, persist sync state in PostgreSQL rather than the reference SQLite store, and route Pub/Sub deliveries through an authenticated endpoint. Keep refresh tokens in encrypted secret storage/KMS. Reconciliation should remain scheduled even when notifications are enabled.
