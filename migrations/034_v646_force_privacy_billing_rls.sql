-- V6.46: close FORCE RLS gaps on tenant tables introduced after V6.22.
-- ENABLE RLS alone is bypassed by the table owner; FORCE keeps the tenant policy
-- active for application connections that own these tables.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'privacy_requests',
    'privacy_consents',
    'billing_transactions'
  ] LOOP
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
  END LOOP;
END $$;
