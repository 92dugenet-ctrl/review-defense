-- V6.20: production foundation metadata and migration bookkeeping.
CREATE TABLE IF NOT EXISTS organization_runtime_settings (
  organization_id uuid PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
  updated_at timestamptz NOT NULL DEFAULT now(),
  settings jsonb NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE organization_runtime_settings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS organization_runtime_settings_org_isolation ON organization_runtime_settings;
CREATE POLICY organization_runtime_settings_org_isolation ON organization_runtime_settings
  USING (organization_id::text = current_setting('app.organization_id', true))
  WITH CHECK (organization_id::text = current_setting('app.organization_id', true));

CREATE INDEX IF NOT EXISTS idx_runtime_settings_updated ON organization_runtime_settings(updated_at DESC);
