# Review Defense V6.21 — Authentication & Security Hardening

V6.21 hardens the production authentication boundary without adding autonomous external actions.

## Added
- Persistent PostgreSQL login using an explicit `organization_id`.
- Authentication attempt rate limiting per source/email key.
- Persistent session creation with user-agent and hashed source-IP metadata.
- Session last-seen updates.
- Persistent revoke-all support.
- Persistent security events for login/logout/session revocation.
- Invitation lookup/acceptance persistence primitives.
- Tenant-scoped member listing persistence primitive.
- API version reports 6.21.

## Security invariants
- Passwords remain PBKDF2-HMAC-SHA256 with the existing password policy.
- Raw session tokens are never persisted; only SHA-256 hashes are stored.
- Source IP is stored only as a SHA-256 hash.
- Authentication requires an organization identifier when using PostgreSQL so lookup remains tenant-scoped under RLS.
- Existing human approval gates and the prohibition on automatic Google mutation remain unchanged.
- No credentials or tokens are logged by the implementation.

## Limitation
V6.21 does not yet provide MFA, password-reset email delivery, or external identity providers. Those should be added only after the core production authentication path is validated end-to-end.
