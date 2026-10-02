-- V6.6: deterministic, unverified evidence fact suggestions.
CREATE TABLE IF NOT EXISTS evidence_fact_suggestions (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  suggestion_id text NOT NULL,
  evidence_id uuid NOT NULL,
  case_id uuid NOT NULL,
  key text NOT NULL,
  kind text NOT NULL,
  value text NOT NULL,
  source_location text NOT NULL DEFAULT '',
  confidence numeric(5,4) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, suggestion_id)
);
CREATE INDEX IF NOT EXISTS idx_fact_suggestions_case ON evidence_fact_suggestions(organization_id, case_id, evidence_id);
ALTER TABLE evidence_fact_suggestions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS evidence_fact_suggestions_org_isolation ON evidence_fact_suggestions;
CREATE POLICY evidence_fact_suggestions_org_isolation ON evidence_fact_suggestions
USING (organization_id::text = current_setting('app.organization_id', true));
