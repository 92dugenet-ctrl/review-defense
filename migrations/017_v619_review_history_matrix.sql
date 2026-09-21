-- V6.19 append-only contradiction disposition history.
CREATE TABLE IF NOT EXISTS contradiction_disposition_history (
  history_id TEXT PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(organization_id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  contradiction_id TEXT NOT NULL,
  disposition_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('CONFIRMED_CONTRADICTION','EXPLAINED','FALSE_POSITIVE','NEEDS_MORE_EVIDENCE')),
  rationale TEXT NOT NULL,
  actor_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  requires_human_review BOOLEAN NOT NULL DEFAULT TRUE
);
ALTER TABLE contradiction_disposition_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contradiction_disposition_history_tenant ON contradiction_disposition_history;
CREATE POLICY contradiction_disposition_history_tenant ON contradiction_disposition_history
  USING (organization_id = current_setting('app.organization_id', true)::uuid)
  WITH CHECK (organization_id = current_setting('app.organization_id', true)::uuid);
CREATE INDEX IF NOT EXISTS idx_contradiction_history_case ON contradiction_disposition_history(organization_id, case_id, contradiction_id, created_at DESC);
