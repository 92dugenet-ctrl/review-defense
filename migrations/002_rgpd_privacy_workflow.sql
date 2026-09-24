-- V6.40 / RGPD approfondi
-- Requests, optional consents and tenant-scoped privacy workflow.
CREATE TABLE IF NOT EXISTS privacy_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  requester_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  request_type text NOT NULL CHECK (request_type IN ('ACCESS','RECTIFICATION','ERASURE','RESTRICTION','OBJECTION','PORTABILITY')),
  status text NOT NULL DEFAULT 'RECEIVED' CHECK (status IN ('RECEIVED','IN_REVIEW','COMPLETED','REJECTED')),
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  response_note text,
  due_at timestamptz NOT NULL DEFAULT (now() + interval '30 days'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_privacy_requests_org_created
  ON privacy_requests (organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_privacy_requests_requester
  ON privacy_requests (requester_user_id, created_at DESC);

ALTER TABLE privacy_requests ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS privacy_requests_org_isolation ON privacy_requests;
CREATE POLICY privacy_requests_org_isolation ON privacy_requests
  USING (organization_id::text = current_setting('app.organization_id', true))
  WITH CHECK (organization_id::text = current_setting('app.organization_id', true));

CREATE TABLE IF NOT EXISTS privacy_consents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  purpose text NOT NULL,
  policy_version text NOT NULL,
  granted boolean NOT NULL,
  granted_at timestamptz NOT NULL DEFAULT now(),
  withdrawn_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_privacy_consents_user
  ON privacy_consents (organization_id, user_id, purpose, granted_at DESC);

ALTER TABLE privacy_consents ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS privacy_consents_org_isolation ON privacy_consents;
CREATE POLICY privacy_consents_org_isolation ON privacy_consents
  USING (organization_id::text = current_setting('app.organization_id', true))
  WITH CHECK (organization_id::text = current_setting('app.organization_id', true));
