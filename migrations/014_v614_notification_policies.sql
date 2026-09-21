-- V6.14 tenant-scoped notification policy.
CREATE TABLE IF NOT EXISTS organization_notification_policies (
  organization_id UUID PRIMARY KEY REFERENCES organizations(organization_id) ON DELETE CASCADE,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  levels TEXT[] NOT NULL DEFAULT ARRAY['DUE','CRITICAL'],
  channels TEXT[] NOT NULL DEFAULT ARRAY['IN_APP','EMAIL','WEBHOOK'],
  quiet_start TIME,
  quiet_end TIME,
  allow_external BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE organization_notification_policies ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS organization_notification_policies_tenant ON organization_notification_policies;
CREATE POLICY organization_notification_policies_tenant ON organization_notification_policies
  USING (organization_id = current_setting('app.organization_id', true)::uuid)
  WITH CHECK (organization_id = current_setting('app.organization_id', true)::uuid);
