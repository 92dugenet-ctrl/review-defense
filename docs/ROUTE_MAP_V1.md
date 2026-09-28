# Review Defense — Route Map V1

This is the canonical conceptual route map while the HTTP layer remains physically implemented in `src/api_server.py`.

| Method | Route family | Context | Client | Internal |
|---|---|---|---:|---:|
| POST | /v1/auth/* | Identity | ✓ | ✓ |
| GET/POST | /v1/me, /v1/logout | Identity | ✓ | ✓ |
| GET/POST | /v1/organization/* | Organization | Limited | ✓ |
| GET/POST | /v1/reviews/* | Reviews | ✓ | ✓ |
| GET/POST | /v1/evidence/* | Evidence | ✓ | ✓ |
| GET/POST | /v1/cases/* | Cases | ✓ | ✓ |
| GET/POST | /v1/review-queue/* | Operations | — | ✓ |
| GET/POST | /v1/escalations/* | Operations | — | ✓ |
| GET/POST | /v1/notifications/* | Notifications | Limited | ✓ |
| GET | /v1/approvals | Decisions | — | ✓ |
| GET | /v1/submissions | Submission | — | ✓ |
| GET | /v1/billing | Billing | ✓ | ✓ |
| GET/POST | /v1/paypal/* | Billing | Limited | ✓ |
| GET/POST | /v1/privacy/* | Privacy | ✓ | ✓ |
| GET | /health | Platform | — | ✓ |
| GET | /ready | Platform | — | ✓ |
| GET | /metrics | Platform | — | ✓ |

## Case route subresources

`/v1/cases/:id` currently contains:

- workspace
- SLA
- pause/resume SLA
- contradictions
- contradiction history
- contradiction disposition
- evidence matrix
- review checklist
- review readiness
- decision
- freeze
- approve
- submit

These operations must remain grouped conceptually under the Case lifecycle but are subject to different authorization policies.

## Route rules

1. Every route belongs to exactly one bounded context.
2. A route must delegate business logic rather than implement it inline.
3. Authorization is server-side.
4. Client routes must never expose admin-only mutations.
5. External integration calls must not be reachable by bypassing their integration boundary.
6. New routes must be added to this map before implementation.
7. No duplicate route definition may become a second source of truth.

## Current physical state

The route map is conceptual. The physical HTTP implementation remains in `src/api_server.py` until a later, separately validated extraction step.
