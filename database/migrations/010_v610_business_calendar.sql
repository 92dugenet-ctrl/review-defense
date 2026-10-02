-- V6.10 tenant business calendar and explicit escalation workflow.
CREATE TABLE IF NOT EXISTS organization_sla_calendars (
  organization_id UUID PRIMARY KEY,
  timezone TEXT NOT NULL DEFAULT 'UTC',
  workdays JSONB NOT NULL DEFAULT '[0,1,2,3,4,5,6]'::jsonb,
  start_hour SMALLINT NOT NULL DEFAULT 0,
  end_hour SMALLINT NOT NULL DEFAULT 24,
  holidays JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE api_cases ADD COLUMN IF NOT EXISTS sla_calendar_timezone TEXT;
CREATE TABLE IF NOT EXISTS case_escalations (
  organization_id UUID NOT NULL,
  case_id UUID NOT NULL,
  level TEXT NOT NULL,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'OPEN',
  acknowledged_by UUID,
  acknowledged_at TIMESTAMPTZ,
  resolved_by UUID,
  resolved_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, case_id, level)
);
CREATE INDEX IF NOT EXISTS idx_case_escalations_org_status ON case_escalations(organization_id, status, updated_at DESC);
