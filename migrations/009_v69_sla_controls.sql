-- V6.9 manual SLA controls. Pauses are explicit analyst actions; no automatic reassignment/escalation action is performed.
ALTER TABLE api_cases ADD COLUMN IF NOT EXISTS sla_paused_at TIMESTAMPTZ;
ALTER TABLE api_cases ADD COLUMN IF NOT EXISTS sla_paused_seconds DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE api_cases ADD COLUMN IF NOT EXISTS sla_pause_reason TEXT;
CREATE INDEX IF NOT EXISTS idx_api_cases_org_sla_pause ON api_cases(organization_id, sla_paused_at, updated_at DESC);
