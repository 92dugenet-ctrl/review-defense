-- V6.47: shared atomic API rate limits across Gunicorn workers.
-- Keys are SHA-256 digests of scoped client identifiers; no raw IP or email is stored.
CREATE TABLE IF NOT EXISTS api_rate_limits (
    key_hash char(64) PRIMARY KEY
        CHECK (key_hash ~ '^[0-9a-f]{64}$'),
    window_started_at timestamptz NOT NULL,
    hit_count integer NOT NULL CHECK (hit_count > 0),
    expires_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_rate_limits_expires_at
    ON api_rate_limits (expires_at);
