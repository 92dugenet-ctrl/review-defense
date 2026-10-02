-- V6.18: explicit human disposition of contradiction findings.
CREATE TABLE IF NOT EXISTS contradiction_dispositions (
  disposition_id UUID PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  contradiction_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('CONFIRMED_CONTRADICTION','EXPLAINED','FALSE_POSITIVE','NEEDS_MORE_EVIDENCE')),
  rationale TEXT NOT NULL,
  actor_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  requires_human_review BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (organization_id, contradiction_id)
);
ALTER TABLE contradiction_dispositions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS contradiction_dispositions_tenant ON contradiction_dispositions;
CREATE POLICY contradiction_dispositions_tenant ON contradiction_dispositions
  USING (organization_id = current_setting('app.organization_id', true)::uuid)
  WITH CHECK (organization_id = current_setting('app.organization_id', true)::uuid);
CREATE INDEX IF NOT EXISTS idx_contradiction_dispositions_case ON contradiction_dispositions(organization_id, case_id, created_at DESC);
