# Review Defense — Architecture Boundaries V1

## Purpose

This document freezes the current architectural boundaries before structural refactoring.

It is an architectural contract, not a code migration. The first implementation step must not change server configuration, deployment configuration, database schema, external credentials, or product behavior.

## 1. System layers

Requests should conceptually follow this direction:

HTTP / Frontend
→ API routing and transport
→ Authentication / Authorization
→ Application service
→ Domain logic
→ Repository / Storage / External integration
→ Infrastructure

Reverse dependencies are forbidden.

### Forbidden direct crossings

- Frontend code must not call internal database or infrastructure interfaces.
- HTTP route handlers must not contain durable-storage implementation details when a service/repository boundary exists.
- Domain modules must not depend on HTTP request/response objects.
- Repositories must not depend on HTTP routing or frontend code.
- External integrations must be isolated behind explicit integration modules.
- Client-facing code must not expose internal operational, security, infrastructure, or administrator-only details.

## 2. Current bounded contexts

### Identity & access
Current primary modules:
- `src/identity.py`
- `src/security_hardening.py`
- `src/mfa.py`
- `src/recovery_email.py`

Responsibilities:
- authentication
- sessions
- roles
- authorization
- MFA
- account recovery
- email verification

### Reviews
Current primary modules:
- `src/review_workspace.py`
- `src/google_business_profile.py`
- `src/google_integration.py`
- `src/google_sync_engine.py`
- `src/google_pubsub_receiver.py`

Responsibilities:
- review ingestion
- review representation
- claims and policy analysis
- controlled Google read/sync integration

### Cases
Current primary modules:
- `src/case_review.py`
- `src/case_review_matrix.py`
- `src/review_queue.py`
- `src/review_sla.py`
- `src/escalation_workflow.py`

Responsibilities:
- dossier lifecycle
- readiness
- evidence requirements
- assignment
- SLA
- escalation

### Evidence
Current primary modules:
- `src/evidence_vault.py`
- `src/evidence_extraction.py`
- `src/evidence_ocr.py`

Responsibilities:
- evidence storage
- integrity
- extraction
- OCR/readable text
- fact suggestions

### Decisions & controlled submission
Current primary modules:
- `src/decision_workspace.py`
- `src/submission_workspace.py`
- `src/outcome_workspace.py`

Responsibilities:
- human decision
- freeze/snapshot
- approval
- controlled preparation/submission
- outcome tracking

### Notifications
Current primary modules:
- `src/notification_outbox.py`
- `src/notification_delivery.py`
- `src/notification_worker.py`
- `src/notification_policy.py`
- `src/notification_observability.py`

Responsibilities:
- notification creation
- delivery
- worker execution
- policies
- observability

### Billing
Current primary modules:
- `src/billing_catalog.py`
- `src/paypal_client.py`

Responsibilities:
- public offers
- PayPal communication
- billing state

### Privacy
Current primary modules:
- privacy routes currently implemented in `src/api_server.py`
- migration/data support under `migrations/`

Responsibilities:
- consent
- privacy requests
- export

### Platform / infrastructure
Current primary modules:
- `src/postgres_repository.py`
- `src/postgres_api_repository.py`
- `src/postgres_integration.py`
- `src/postgres_sync.py`
- `src/deployment.py`
- `src/production_config.py`
- `src/observability.py`
- `src/resilience.py`

Responsibilities:
- persistence
- configuration
- deployment
- telemetry
- resilience

## 3. HTTP route ownership

Until routes are physically split, `src/api_server.py` remains the HTTP composition root.

Route families are owned conceptually as follows:

| Prefix | Owner |
|---|---|
| `/v1/auth/*` | Identity |
| `/v1/me` | Identity |
| `/v1/logout` | Identity |
| `/v1/organization/*` | Organization / Access |
| `/v1/reviews/*` | Reviews |
| `/v1/evidence/*` | Evidence |
| `/v1/cases/*` | Cases |
| `/v1/review-queue/*` | Cases / Operations |
| `/v1/escalations/*` | Cases / Operations |
| `/v1/notifications/*` | Notifications |
| `/v1/approvals` | Decisions |
| `/v1/submissions` | Decisions / Submission |
| `/v1/billing` | Billing |
| `/v1/paypal/*` | Billing / PayPal integration |
| `/v1/privacy/*` | Privacy |
| `/health`, `/ready`, `/metrics` | Platform |

This table is the source of truth for future route extraction.

## 4. Authorization boundary

### Client

Allowed:
- create/submit a dossier
- provide evidence
- consult own dossier
- consult customer-safe status/readiness information
- respond to requested information

Forbidden:
- decision
- freeze
- approval
- submission
- SLA control
- contradiction analysis/disposition
- administrative notification operations
- evidence/fact verification
- review checklist completion on behalf of operations

### Internal roles

- OWNER / ADMIN: administrative and human-gated decision operations.
- ANALYST: analysis/review operations allowed by the existing authorization policy.
- VIEWER: read-only access allowed by the existing authorization policy.

Authorization must be enforced server-side. Frontend visibility is not a security boundary.

## 5. Data ownership

Each bounded context owns its data semantics.

- Cases own lifecycle and case state.
- Reviews own review representation and analysis inputs.
- Evidence owns evidence metadata, integrity and extraction state.
- Decisions own decision/freeze/approval state.
- Notifications own notification state.
- Billing owns billing state.
- Identity owns identity/session state.

Cross-context access should happen through explicit service/repository contracts rather than direct mutation of another context's internal structures.

## 6. External integrations

External systems must be isolated:

- Google integration is read/sync oriented and must not bypass the human-gated decision boundary.
- PayPal is accessed through the billing/integration boundary.
- Email delivery is accessed through notification/recovery boundaries.
- PostgreSQL is accessed through repository/infrastructure boundaries.

No business module should embed credentials, raw external HTTP clients, or deployment-specific configuration.

## 7. Composition root

`src/api_server.py` is currently the composition root.

Future refactoring should make it progressively thinner:

1. route matching
2. request decoding
3. authentication context
4. delegation to service
5. response serialization
6. error translation

Business decisions belong outside the composition root.

## 8. Frontend boundary

Frontend modules are divided conceptually into:

- public/marketing pages
- authenticated console shell
- routing/navigation
- reusable UI components
- API interaction
- customer-facing case/evidence/status views
- internal operational views

Customer UI must consume customer-safe API contracts rather than reconstructing internal state or exposing internal identifiers/roles/implementation details.

## 9. Refactoring rules

Before any structural move:

1. Preserve current API behavior unless a separate product change is explicitly approved.
2. Preserve database schema and migrations.
3. Preserve external server configuration.
4. Move one bounded context at a time.
5. Keep the old and new route contract covered during migration.
6. Run the existing regression workflow after each atomic change.
7. Do not combine architecture cleanup with UX/product changes in the same commit.
8. Do not delete historical migrations.
9. Do not create duplicate sources of truth for routes, roles, statuses, or domain state.
10. Every moved responsibility must have one clear owner.

## 10. Target dependency direction

`HTTP → Application → Domain → Ports → Infrastructure`

Allowed infrastructure adapters:
- PostgreSQL
- filesystem/object storage
- Google
- PayPal
- email
- telemetry

Infrastructure must not become a second application layer.

## 11. Frozen baseline

This architecture document is introduced from the current green baseline.

It does not authorize:
- frontend redesign
- database migration
- server configuration changes
- role-policy changes
- external integration behavior changes
- automatic Google actions

Those remain separate changes requiring their own commits and workflow validation.
