-- V6.41 client monitoring hub: organization profile, client documents and Google connections.
CREATE TABLE IF NOT EXISTS organization_profiles (
  organization_id uuid PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
  legal_name text,
  website text,
  phone text,
  address text,
  city text,
  postal_code text,
  country text,
  sector text,
  employee_count text,
  description text,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS client_documents (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filename text NOT NULL,
  content_type text NOT NULL,
  size_bytes bigint NOT NULL,
  sha256 text NOT NULL,
  object_key text NOT NULL,
  category text NOT NULL DEFAULT 'GENERAL',
  created_by uuid REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS google_connections (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  connection_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  google_account_id text,
  google_location_id text,
  location_title text,
  encrypted_access_token text NOT NULL,
  encrypted_refresh_token text,
  expires_at timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'CONNECTED',
  created_by uuid REFERENCES users(id),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS google_oauth_states (
  state text PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  code_verifier text NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_client_documents_org_created ON client_documents(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_google_connections_org ON google_connections(organization_id, updated_at DESC);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['organization_profiles','client_documents','google_connections','google_oauth_states'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS %I_org_isolation ON %I', t, t);
    EXECUTE format('CREATE POLICY %I_org_isolation ON %I USING (organization_id::text = current_setting(''app.organization_id'', true))', t, t);
  END LOOP;
END $$;
