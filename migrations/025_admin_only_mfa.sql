-- V6.40+: MFA is an administrator-only control.
-- Existing client-facing accounts must not retain an active MFA requirement.
-- Roles are stored on memberships, not users. Keep MFA only for users who
-- have at least one administrator membership in any organization.
UPDATE users
SET mfa_enabled = false,
    mfa_secret_enc = NULL,
    mfa_enabled_at = NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM memberships
    WHERE memberships.user_id = users.id
      AND memberships.role IN ('OWNER', 'ADMIN')
);
