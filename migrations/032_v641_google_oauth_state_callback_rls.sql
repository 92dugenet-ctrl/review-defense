-- Allow an OAuth callback, which has no authenticated tenant yet, to consume only its exact signed state.
-- Tenant-scoped reads/writes continue to use the existing organization isolation policy.
CREATE POLICY google_oauth_state_callback_lookup
  ON google_oauth_states FOR SELECT
  USING (state = current_setting('app.google_oauth_state', true));

CREATE POLICY google_oauth_state_callback_consume
  ON google_oauth_states FOR DELETE
  USING (state = current_setting('app.google_oauth_state', true));

CREATE INDEX IF NOT EXISTS idx_google_oauth_states_expires
  ON google_oauth_states(expires_at);
