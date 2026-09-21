-- V6.5: explicit structured facts and deterministic contradiction findings.
CREATE TABLE IF NOT EXISTS evidence_facts (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  fact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evidence_id uuid NOT NULL,
  case_id uuid NOT NULL,
  key text NOT NULL,
  kind text NOT NULL,
  value text NOT NULL,
  source_location text NOT NULL DEFAULT '',
  verified boolean NOT NULL DEFAULT false,
  verified_by uuid REFERENCES users(id) ON DELETE SET NULL,
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_evidence_facts_case ON evidence_facts(organization_id, case_id, evidence_id);

CREATE TABLE IF NOT EXISTS contradiction_findings (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  contradiction_id text NOT NULL,
  case_id uuid NOT NULL,
  claim_id text NOT NULL,
  key text NOT NULL,
  kind text NOT NULL,
  claim_value text NOT NULL,
  evidence_ids jsonb NOT NULL,
  evidence_values jsonb NOT NULL,
  description text NOT NULL,
  confidence numeric(5,4) NOT NULL,
  requires_human_review boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, contradiction_id)
);
CREATE INDEX IF NOT EXISTS idx_contradictions_case ON contradiction_findings(organization_id, case_id, created_at DESC);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['evidence_facts','contradiction_findings'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS %I_org_isolation ON %I', t, t);
    EXECUTE format('CREATE POLICY %I_org_isolation ON %I USING (organization_id::text = current_setting(''app.organization_id'', true))', t, t);
  END LOOP;
END $$;
