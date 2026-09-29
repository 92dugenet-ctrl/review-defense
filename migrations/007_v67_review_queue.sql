-- V6.7 analyst review queue assignment.
ALTER TABLE api_cases ADD COLUMN IF NOT EXISTS assigned_to uuid;
CREATE INDEX IF NOT EXISTS idx_api_cases_org_assigned_updated ON api_cases(organization_id, assigned_to, updated_at DESC);
