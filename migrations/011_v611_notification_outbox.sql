-- V6.11 auditable notification outbox. No delivery/network side effects are performed by the API.
CREATE TABLE IF NOT EXISTS notification_outbox (
  organization_id UUID NOT NULL,
  notification_id UUID NOT NULL,
  case_id UUID NOT NULL,
  escalation_level TEXT NOT NULL,
  channel TEXT NOT NULL,
  target TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  created_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_by UUID,
  sent_at TIMESTAMPTZ,
  cancelled_by UUID,
  cancelled_at TIMESTAMPTZ,
  dedupe_key TEXT NOT NULL,
  PRIMARY KEY (organization_id, notification_id),
  UNIQUE (organization_id, dedupe_key),
  CONSTRAINT notification_outbox_channel_chk CHECK (channel IN ('IN_APP','EMAIL','WEBHOOK')),
  CONSTRAINT notification_outbox_status_chk CHECK (status IN ('PENDING','SENT','CANCELLED'))
);
CREATE INDEX IF NOT EXISTS idx_notification_outbox_org_status ON notification_outbox(organization_id, status, created_at DESC);
ALTER TABLE notification_outbox ENABLE ROW LEVEL SECURITY;
CREATE POLICY notification_outbox_org_isolation ON notification_outbox
  USING (organization_id::text = current_setting('app.organization_id', true));
