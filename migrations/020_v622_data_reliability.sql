-- V6.22: production data reliability and defense-in-depth RLS.
-- Every tenant-owned table is forced through RLS and receives both read and write checks.
DO $$
DECLARE
  r record;
BEGIN
  FOR r IN
    SELECT DISTINCT c.relname AS table_name
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'organization_id' AND NOT a.attisdropped
    WHERE n.nspname = 'public' AND c.relkind = 'r'
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', r.table_name);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', r.table_name);
    EXECUTE format('DROP POLICY IF EXISTS %I_org_isolation ON %I', r.table_name, r.table_name);
    EXECUTE format(
      'CREATE POLICY %I_org_isolation ON %I USING (organization_id::text = current_setting(''app.organization_id'', true)) WITH CHECK (organization_id::text = current_setting(''app.organization_id'', true))',
      r.table_name, r.table_name
    );
  END LOOP;
END $$;

CREATE INDEX IF NOT EXISTS idx_api_sessions_expiry ON api_sessions(expires_at, revoked_at);
CREATE INDEX IF NOT EXISTS idx_security_events_actor_created ON security_events(actor_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_case_events_org_created ON case_events(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_evidence_case_created ON api_evidence(organization_id, case_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_idempotency_created ON api_idempotency(organization_id, created_at DESC);

CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$fn$$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$fn$$;

DROP TRIGGER IF EXISTS trg_cases_updated_at ON cases;
CREATE TRIGGER trg_cases_updated_at BEFORE UPDATE ON cases FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
DROP TRIGGER IF EXISTS trg_api_cases_updated_at ON api_cases;
CREATE TRIGGER trg_api_cases_updated_at BEFORE UPDATE ON api_cases FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Make existing session timestamps deterministic for rows created before V6.21.
UPDATE api_sessions SET last_seen_at = COALESCE(last_seen_at, created_at) WHERE last_seen_at IS NULL;
