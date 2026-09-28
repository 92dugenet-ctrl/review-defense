-- V6.24: MFA enrollment/state and password-recovery tokens.
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled boolean NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_secret_enc text;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled_at timestamptz;
CREATE TABLE IF NOT EXISTS password_recovery_tokens (
  recovery_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash text NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL,
  used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE password_recovery_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_recovery_tokens FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS password_recovery_tokens_org_isolation ON password_recovery_tokens;
CREATE POLICY password_recovery_tokens_org_isolation ON password_recovery_tokens
  USING (organization_id::text = current_setting('app.organization_id', true))
  WITH CHECK (organization_id::text = current_setting('app.organization_id', true));
CREATE INDEX IF NOT EXISTS idx_recovery_token_hash ON password_recovery_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_recovery_user_created ON password_recovery_tokens(organization_id,user_id,created_at DESC);
