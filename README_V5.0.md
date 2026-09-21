# Review Defense V5.0 — Security Hardening

Production-oriented security primitives added to the framework-neutral reference layer.

## Included
- PBKDF2-SHA256 salted password hashing and constant-time verification.
- Opaque session tokens with SHA-256 storage, expiration and revocation checks.
- Explicit organization/tenant boundary enforcement.
- Fixed-window rate limiter for authentication/API protection.
- Upload size, MIME type and filename validation.
- SHA-256 content integrity helper.
- External-reference validation.
- Security role gates for OWNER/ADMIN security administration.

## Boundaries
This is a reference/application layer, not a deployed security perimeter. Production deployment must additionally enforce TLS, secret management, secure cookies, CSRF protections where applicable, reverse-proxy limits, centralized rate limiting, malware scanning, object-storage policies, database RLS/transactions, key rotation, monitoring and incident response.

No Google submission or external network action is performed by this module.
