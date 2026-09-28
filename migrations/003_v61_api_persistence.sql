-- V6.1: persistent API/application state. All tenant-owned rows are RLS protected.
CREATE TABLE IF NOT EXISTS api_sessions (
  token_hash text PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('OWNER','ADMIN','ANALYST','CLIENT','VIEWER')),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_api_sessions_org ON api_sessions(organization_id);

CREATE TABLE IF NOT EXISTS api_reviews (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  review_id text NOT NULL,
  location_id text NOT NULL DEFAULT '',
  author_display_name text,
  rating smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
  review_text text NOT NULL,
  published_at text,
  updated_at text,
  language text,
  source text NOT NULL,
  review_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, review_id)
);

CREATE TABLE IF NOT EXISTS api_cases (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  case_id uuid NOT NULL,
  review_id text NOT NULL,
  status text NOT NULL,
  decision_id uuid,
  snapshot_sha256 text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, case_id),
  UNIQUE (organization_id, review_id, case_id)
);
CREATE INDEX IF NOT EXISTS idx_api_cases_org_updated ON api_cases(organization_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS api_decisions (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  decision_id uuid NOT NULL,
  case_id uuid NOT NULL,
  status text NOT NULL,
  kind text NOT NULL,
  rationale text NOT NULL,
  snapshot_sha256 text,
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, decision_id)
);

CREATE TABLE IF NOT EXISTS api_dossier_snapshots (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  case_id uuid NOT NULL,
  sha256 text NOT NULL,
  payload jsonb NOT NULL,
  frozen_by uuid,
  frozen_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, case_id)
);

CREATE TABLE IF NOT EXISTS api_approvals (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  approval_id uuid NOT NULL,
  case_id uuid NOT NULL,
  decision_id uuid NOT NULL,
  actor_id uuid NOT NULL,
  actor_role text NOT NULL,
  snapshot_sha256 text NOT NULL,
  approved_at timestamptz NOT NULL,
  PRIMARY KEY (organization_id, approval_id)
);

CREATE TABLE IF NOT EXISTS api_submissions (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  submission_id uuid NOT NULL,
  case_id uuid NOT NULL,
  status text NOT NULL,
  external_call boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, submission_id)
);

CREATE TABLE IF NOT EXISTS api_idempotency (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  idempotency_key text NOT NULL,
  payload_fingerprint text NOT NULL,
  response_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS api_evidence (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  evidence_id uuid NOT NULL,
  case_id uuid NOT NULL,
  filename text NOT NULL,
  content_type text NOT NULL,
  size_bytes bigint NOT NULL,
  sha256 text NOT NULL,
  object_key text NOT NULL,
  verified boolean NOT NULL DEFAULT false,
  created_by uuid,
  verified_by uuid,
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, evidence_id)
);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['api_sessions','api_reviews','api_cases','api_decisions','api_dossier_snapshots','api_approvals','api_submissions','api_idempotency','api_evidence'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS %I_org_isolation ON %I', t, t);
    EXECUTE format('CREATE POLICY %I_org_isolation ON %I USING (organization_id::text = current_setting(''app.organization_id'', true))', t, t);
  END LOOP;
END $$;
