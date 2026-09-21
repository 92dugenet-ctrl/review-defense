# Review Defense V6.2 — Production Authentication & Identity

V6.2 hardens the identity boundary around the V6.0 HTTP API and V6.1 PostgreSQL persistence layer.

## Implemented
- Canonical email validation/normalization.
- Central role validation for OWNER/ADMIN/ANALYST/CLIENT/VIEWER.
- Secure session issuance with bounded TTL.
- Session rotation: old bearer token is immediately revoked.
- Password change with PBKDF2-SHA256, existing password verification and global session revocation.
- Fresh session issued after password change.
- Owner/admin global session revocation for a target member.
- Persistent role changes with session invalidation.
- Organization member listing.
- Organization invitations with hashed one-time invitation tokens and bounded expiry.
- Public invitation acceptance with password creation/update and automatic session issuance.
- Invitation tokens are returned once and are not stored in clear text.
- Security-event persistence boundary in PostgreSQL.
- PostgreSQL persistence hooks for password changes, session revocation, role changes, invitations and security events.
- Existing tenant RLS and `SET LOCAL app.organization_id` boundaries preserved.
- No Google mutation or external submission is introduced by the identity layer.

## API additions
- `POST /v1/auth/rotate`
- `POST /v1/auth/change-password`
- `POST /v1/auth/revoke-all`
- `GET /v1/organization/members`
- `POST /v1/organization/members/{user_id}/role`
- `POST /v1/organization/invitations`
- `POST /v1/organization/invitations/accept`

## Security invariants
- Tenant cannot be selected through request parameters after authentication.
- Client/viewer roles cannot manage organization identity.
- Only OWNER can grant/demote OWNER.
- Password changes revoke all prior sessions.
- Rotation revokes the previous session.
- Invitation acceptance is single-use and time-bounded.
- Tokens are stored only as hashes.

## Validation
175 tests pass with `pytest -q`.
