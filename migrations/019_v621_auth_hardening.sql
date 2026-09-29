-- V6.21: authentication persistence, security-event metadata, and session revocation.
ALTER TABLE api_sessions ADD COLUMN IF NOT EXISTS last_seen_at timestamptz;
ALTER TABLE api_sessions ADD COLUMN IF NOT EXISTS user_agent text;
ALTER TABLE api_sessions ADD COLUMN IF NOT EXISTS ip_hash text;
CREATE INDEX IF NOT EXISTS idx_api_sessions_user ON api_sessions(organization_id,user_id,created_at DESC);

ALTER TABLE organization_invitations ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
CREATE INDEX IF NOT EXISTS idx_org_invites_token_hash ON organization_invitations(token_hash);

ALTER TABLE security_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS security_events_org_isolation ON security_events;
CREATE POLICY security_events_org_isolation ON security_events
  USING (organization_id::text = current_setting('app.organization_id', true))
  WITH CHECK (organization_id::text = current_setting('app.organization_id', true));
