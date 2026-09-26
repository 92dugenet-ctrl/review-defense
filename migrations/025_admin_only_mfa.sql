-- V6.40+: MFA is an administrator-only control.
-- Existing client-facing accounts must not retain an active MFA requirement.
UPDATE users
SET mfa_enabled = false,
    mfa_secret_enc = NULL,
    mfa_enabled_at = NULL
WHERE role NOT IN ('OWNER', 'ADMIN');
