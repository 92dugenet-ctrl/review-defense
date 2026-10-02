-- V6.45: enforce tenant policies even when the application connects as a table owner.
-- PostgreSQL table owners normally bypass RLS unless FORCE ROW LEVEL SECURITY is enabled.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'organization_profiles',
    'client_documents',
    'google_connections',
    'google_oauth_states'
  ] LOOP
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
  END LOOP;
END $$;
