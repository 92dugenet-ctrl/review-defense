# Review Defense V6.24 — Advanced Authentication

V6.24 adds optional TOTP MFA and secure password recovery.

## MFA
- RFC 6238-compatible TOTP with ±1 step clock tolerance.
- Enrollment returns an `otpauth://` URI and secret once.
- The secret is encrypted at rest with Fernet. Production requires `REVIEW_DEFENSE_MFA_ENCRYPTION_KEY`.
- Login requires a valid `mfa_code` when MFA is enabled.
- MFA confirmation and disabling are audited.
- Disabling MFA is restricted to OWNER/ADMIN and requires the current password and, when enabled, a valid TOTP.

## Password recovery
- Recovery tokens are cryptographically random, stored only as SHA-256 hashes, expire after 30 minutes, and are single-use.
- Reset revokes all active sessions and changes the password atomically through the persistence boundary.
- Unknown accounts receive the same generic response to reduce account enumeration.
- Clear recovery tokens are exposed only when explicitly enabled in development with `REVIEW_DEFENSE_EXPOSE_RECOVERY_TOKEN=true`; never in production.

## Security invariants
- Tenant isolation and RLS are preserved.
- Google deletion/report/reply actions remain human-approved only.
- MFA/recovery cannot directly trigger external Google actions.

## Limitations
A production email delivery path for recovery links is not silently assumed; the recovery token must be delivered through a configured email workflow before public launch.
