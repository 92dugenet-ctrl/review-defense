-- Enforce the tenant and callback-state policies even when the application
-- connects as the owner of these tables. Superusers still bypass PostgreSQL RLS;
-- the application DSN must therefore never use a superuser role.
ALTER TABLE organization_profiles FORCE ROW LEVEL SECURITY;
ALTER TABLE client_documents FORCE ROW LEVEL SECURITY;
ALTER TABLE google_connections FORCE ROW LEVEL SECURITY;
ALTER TABLE google_oauth_states FORCE ROW LEVEL SECURITY;
