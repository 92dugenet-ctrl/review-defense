-- V6.12 controlled notification delivery metadata.
ALTER TABLE notification_outbox ADD COLUMN IF NOT EXISTS delivery_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE notification_outbox ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ;
ALTER TABLE notification_outbox ADD COLUMN IF NOT EXISTS delivery_error TEXT;
CREATE INDEX IF NOT EXISTS idx_notification_outbox_pending_attempts ON notification_outbox(organization_id, status, delivery_attempts, created_at);
