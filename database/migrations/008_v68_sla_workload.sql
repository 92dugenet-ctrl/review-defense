-- V6.8 SLA/workload metadata. Due times remain deterministic from created_at and priority;
-- no automated assignment or external action is introduced.
CREATE INDEX IF NOT EXISTS idx_api_cases_org_updated_assigned ON api_cases(organization_id, updated_at DESC, assigned_to);
