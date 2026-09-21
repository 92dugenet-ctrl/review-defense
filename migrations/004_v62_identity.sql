-- V6.2: production authentication and organization identity.
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at timestamptz NOT NULL DEFAULT now();

CREATE TABLE IF NOT EXISTS organization_invitations (
  invitation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email citext NOT NULL,
  role text NOT NULL CHECK (role IN ('OWNER','ADMIN','ANALYST','CLIENT','VIEWER')),
  token_hash text NOT NULL UNIQUE,
  invited_by uuid NOT NULL REFERENCES users(id),
  expires_at timestamptz NOT NULL,
  accepted_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_org_invites_org ON organization_invitations(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_org_invites_email ON organization_invitations(email);

CREATE TABLE IF NOT EXISTS security_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid REFERENCES organizations(id) ON DELETE CASCADE,
  actor_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  event_type text NOT NULL,
  target_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_security_events_org_created ON security_events(organization_id, created_at DESC);

ALTER TABLE api_sessions ADD COLUMN IF NOT EXISTS last_seen_at timestamptz;
ALTER TABLE api_sessions ADD COLUMN IF NOT EXISTS user_agent text;
ALTER TABLE api_sessions ADD COLUMN IF NOT EXISTS ip_hash text;

ALTER TABLE organization_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS organization_invitations_org_isolation ON organization_invitations;
CREATE POLICY organization_invitations_org_isolation ON organization_invitations USING (organization_id::text = current_setting('app.organization_id', true));
DROP POLICY IF EXISTS security_events_org_isolation ON security_events;
CREATE POLICY security_events_org_isolation ON security_events USING (organization_id::text = current_setting('app.organization_id', true));
