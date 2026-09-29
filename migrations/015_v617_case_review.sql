-- V6.17 analyst checklist; advisory only and tenant-scoped.
CREATE TABLE IF NOT EXISTS case_review_checklist (
  item_id UUID PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  label TEXT NOT NULL,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  completed BOOLEAN NOT NULL DEFAULT FALSE,
  completed_by UUID,
  completed_at TIMESTAMPTZ,
  note TEXT,
  UNIQUE (organization_id, case_id, code)
);
ALTER TABLE case_review_checklist ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS case_review_checklist_tenant ON case_review_checklist;
CREATE POLICY case_review_checklist_tenant ON case_review_checklist
  USING (organization_id = current_setting('app.organization_id', true)::uuid)
  WITH CHECK (organization_id = current_setting('app.organization_id', true)::uuid);
CREATE INDEX IF NOT EXISTS idx_case_review_checklist_case ON case_review_checklist(organization_id, case_id);
