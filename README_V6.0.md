# Review Defense V6.0 — Production API & Application Server

V6.0 adds a framework-neutral HTTP API boundary over the existing Review Defense modules.

## Implemented
- WSGI HTTP application with `/health` and `/ready` probes.
- Bearer session authentication using V5.0 password/session primitives.
- Session expiration and logout.
- Tenant binding from authenticated session; clients cannot override `organization_id`.
- RBAC for analyst/admin/owner mutations.
- Normalized JSON errors and validation responses.
- Rate limiting at the HTTP boundary.
- Idempotency-Key support with payload-fingerprint conflict detection.
- Review ingestion and analysis endpoint.
- Case creation, decision, dossier freeze, approval and submission-preparation endpoints.
- Dossier approval remains explicitly human-gated.
- Submission endpoint only prepares a local submission artifact; it never calls Google.
- Audit events for authentication and state-changing API operations.
- Existing PostgreSQL/object-storage/Google adapters remain injectable boundaries rather than hidden network calls.

## Routes
- `GET /health`
- `GET /ready`
- `POST /v1/auth/login`
- `POST /v1/logout`
- `GET /v1/me`
- `POST /v1/reviews`
- `GET /v1/reviews`
- `GET /v1/reviews/{id}`
- `POST /v1/cases`
- `GET /v1/cases`
- `GET /v1/cases/{id}`
- `POST /v1/cases/{id}/decision`
- `POST /v1/cases/{id}/freeze`
- `POST /v1/cases/{id}/approve`
- `POST /v1/cases/{id}/submit`

## Production boundary
The included server uses an in-memory reference store for deterministic tests. A production deployment should wire PostgreSQL repositories, a durable session/token store, TLS/reverse proxy, secret management, structured observability, and a real WSGI/ASGI server. No Google mutation is performed by V6.0.
- `POST /v1/evidence`
- `GET /v1/evidence`
- `GET /v1/evidence/{id}`
- `POST /v1/evidence/{id}/verify`
- `GET /v1/approvals`
- `GET /v1/submissions`
