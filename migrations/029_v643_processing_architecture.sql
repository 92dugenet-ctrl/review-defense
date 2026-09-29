-- Canonical asynchronous processing model; legacy background_jobs stays compatible.
CREATE TABLE IF NOT EXISTS processing_jobs(
 job_id UUID PRIMARY KEY, organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
 kind TEXT NOT NULL, payload JSONB NOT NULL DEFAULT '{}'::jsonb,
 status TEXT NOT NULL CHECK(status IN('pending','processing','completed','failed')),
 attempt INTEGER NOT NULL DEFAULT 0 CHECK(attempt>=0), max_attempts INTEGER NOT NULL DEFAULT 3 CHECK(max_attempts>=1),
 next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), idempotency_key TEXT, payload_fingerprint TEXT NOT NULL,
 worker_id TEXT, leased_until TIMESTAMPTZ, request_id TEXT, correlation_id TEXT, last_error TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(organization_id,idempotency_key));
CREATE INDEX IF NOT EXISTS idx_processing_jobs_ready ON processing_jobs(status,next_attempt_at,created_at);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_leases ON processing_jobs(status,leased_until);
CREATE TABLE IF NOT EXISTS processing_job_events(
 event_id UUID PRIMARY KEY,job_id UUID NOT NULL REFERENCES processing_jobs(job_id) ON DELETE CASCADE,
 organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,event_type TEXT NOT NULL,
 from_status TEXT,to_status TEXT NOT NULL CHECK(to_status IN('pending','processing','completed','failed')),
 attempt INTEGER NOT NULL CHECK(attempt>=0),worker_id TEXT,request_id TEXT,correlation_id TEXT,
 details JSONB NOT NULL DEFAULT '{}'::jsonb,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE INDEX IF NOT EXISTS idx_processing_job_events_job ON processing_job_events(job_id,created_at);
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY; ALTER TABLE processing_jobs FORCE ROW LEVEL SECURITY;
ALTER TABLE processing_job_events ENABLE ROW LEVEL SECURITY; ALTER TABLE processing_job_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS processing_jobs_tenant_isolation ON processing_jobs;
CREATE POLICY processing_jobs_tenant_isolation ON processing_jobs USING(organization_id=current_setting('app.organization_id',true)::uuid) WITH CHECK(organization_id=current_setting('app.organization_id',true)::uuid);
DROP POLICY IF EXISTS processing_job_events_tenant_isolation ON processing_job_events;
CREATE POLICY processing_job_events_tenant_isolation ON processing_job_events USING(organization_id=current_setting('app.organization_id',true)::uuid) WITH CHECK(organization_id=current_setting('app.organization_id',true)::uuid);
