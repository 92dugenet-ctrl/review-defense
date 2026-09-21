-- V6.13 bounded notification worker state.
ALTER TABLE notification_outbox ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3;
ALTER TABLE notification_outbox ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ;
ALTER TABLE notification_outbox ADD COLUMN IF NOT EXISTS dead_lettered_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_notification_outbox_worker
  ON notification_outbox (organization_id, status, next_attempt_at, created_at);
