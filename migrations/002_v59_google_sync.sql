-- V5.9: PostgreSQL production sync state, Pub/Sub events and jobs.
CREATE TABLE IF NOT EXISTS google_sync_cursors (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  account_id text NOT NULL,
  location_id text NOT NULL,
  next_page_token text,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, account_id, location_id)
);
CREATE TABLE IF NOT EXISTS google_processed_events (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  event_id text NOT NULL,
  processed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, event_id)
);
CREATE TABLE IF NOT EXISTS google_reviews (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  review_id text NOT NULL,
  account_id text NOT NULL,
  location_id text NOT NULL,
  rating smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
  review_text text NOT NULL DEFAULT '',
  author_display_name text,
  published_at timestamptz,
  updated_at timestamptz,
  language text,
  review_url text,
  fingerprint text NOT NULL,
  raw_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  observed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, review_id)
);
CREATE TABLE IF NOT EXISTS background_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  kind text NOT NULL,
  payload jsonb NOT NULL,
  state text NOT NULL,
  priority integer NOT NULL DEFAULT 0,
  attempts integer NOT NULL DEFAULT 0,
  max_attempts integer NOT NULL,
  run_after timestamptz NOT NULL DEFAULT now(),
  idempotency_key text,
  payload_fingerprint text NOT NULL,
  lease_owner text,
  leased_until timestamptz,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_bg_jobs_ready ON background_jobs(state, run_after, priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_bg_jobs_lease ON background_jobs(state, leased_until);
ALTER TABLE google_sync_cursors ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_processed_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE background_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY google_sync_cursor_org_isolation ON google_sync_cursors USING (organization_id::text = current_setting('app.organization_id', true));
CREATE POLICY google_events_org_isolation ON google_processed_events USING (organization_id::text = current_setting('app.organization_id', true));
CREATE POLICY google_reviews_org_isolation ON google_reviews USING (organization_id::text = current_setting('app.organization_id', true));
CREATE POLICY bg_jobs_org_isolation ON background_jobs USING (organization_id::text = current_setting('app.organization_id', true));

-- Job claim uses SELECT ... FOR UPDATE SKIP LOCKED inside the repository transaction.
