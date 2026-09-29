-- V6.43 security hardening: MFA replay protection and token uniqueness.
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_last_counter bigint;

CREATE UNIQUE INDEX IF NOT EXISTS uq_password_recovery_token_hash
  ON password_recovery_tokens(token_hash);

CREATE UNIQUE INDEX IF NOT EXISTS uq_email_verification_token_hash
  ON email_verification_tokens(token_hash);

CREATE UNIQUE INDEX IF NOT EXISTS uq_api_session_token_hash
  ON api_sessions(token_hash);
