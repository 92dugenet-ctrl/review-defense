-- V6.40: restore a persisted API session before tenant context is known.
--
-- api_sessions is RLS-protected by organization_id. Authentication starts with
-- only the opaque bearer token, so a narrowly scoped SECURITY DEFINER lookup is
-- required to recover the tenant safely before normal tenant-scoped queries.
CREATE OR REPLACE FUNCTION lookup_api_session_by_token_hash(p_token_hash text)
RETURNS TABLE (
  token_hash text,
  user_id uuid,
  organization_id uuid,
  role text,
  expires_at timestamptz,
  revoked_at timestamptz
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  SELECT s.token_hash, s.user_id, s.organization_id, s.role, s.expires_at, s.revoked_at
  FROM public.api_sessions AS s
  WHERE s.token_hash = p_token_hash
  LIMIT 1;
$$;

REVOKE ALL ON FUNCTION lookup_api_session_by_token_hash(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION lookup_api_session_by_token_hash(text) TO CURRENT_USER;
