# Review Defense V6.25 — Recovery Email & Production Identity

V6.25 completes the authentication-email production layer on top of V6.24.

## Recovery email
- Password-recovery requests can send transactional SMTP email.
- Recovery links are built from a configured public HTTPS base URL in production.
- Recovery tokens remain random, hashed at rest, single-use, and 30-minute limited.
- The public recovery endpoint remains account-enumeration resistant.
- Email delivery failures are audited without exposing whether an account exists.

Enable with:
- `REVIEW_DEFENSE_RECOVERY_EMAIL_ENABLED=true`
- `REVIEW_DEFENSE_PUBLIC_BASE_URL=https://...`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_SENDER`, `SMTP_STARTTLS`

## Email verification
- Users have `email_verified_at` persisted in PostgreSQL.
- Verification tokens are hashed, single-use, expire after 24 hours, and are tenant-scoped.
- `POST /v1/auth/email-verification/request` sends a verification message.
- `POST /v1/auth/email-verification/verify` consumes the token.
- `REVIEW_DEFENSE_REQUIRE_EMAIL_VERIFICATION=true` blocks login until verified.
- Invitation acceptance can require verification and will not issue a session first.

## Security
- SMTP credentials are supplied through runtime configuration, never stored in the repository.
- Production authentication links require HTTPS.
- Google deletion/report/reply actions remain human-approved only.
- Tenant isolation, RLS, evidence integrity, approval gates, and auditability remain unchanged.

## Validation
- 279 tests pass.
- 1 PostgreSQL integration test remains skipped when no dedicated PostgreSQL test database is configured.
- SMTP delivery is tested with an injected transport; no live external email is sent by the test suite.

## Remaining production dependency
Before public launch, configure a dedicated SMTP provider and a real HTTPS `REVIEW_DEFENSE_PUBLIC_BASE_URL`, then execute the PostgreSQL integration suite against a disposable production-like database.
