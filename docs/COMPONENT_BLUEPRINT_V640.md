# Review Defense — V6.40 Component Blueprint

## Objective

Extend the existing V6.40 monolithic frontend with a small, reusable presentation layer without introducing React, a second frontend, or duplicated business logic.

## Component contract

| Component | Inputs | States | Data boundary | Sensitive action |
|---|---|---|---|---|
| Button | label, variant, attributes | default / hover / focus / disabled / loading | presentation only | never authorizes by itself |
| StatusBadge | status, optional label | semantic status tone | server-derived status | none |
| KpiCard | label, value, caption, tone | populated / empty | server/API data | none |
| EmptyState | title, body | empty | none | none |
| ErrorState | title, body | error | API/client error | none |
| LoadingState | none | loading | none | none |
| EvidenceCard | evidence metadata + SHA-256 | loading / populated / missing hash | evidence API | no mutation |
| Timeline | event list | populated / empty | audit/workflow data | read-only |
| ApprovalGate | approval id + status | pending / approved / rejected | approval API | must remain human-gated |

## Required visual rules

- White/surface cards on #F8FAFC.
- #E2E8F0 borders and restrained shadows.
- One primary accent for actions and active states.
- Status colors communicate state, not truth or legal outcome.
- Mobile layouts collapse to one column.
- Focus-visible states remain keyboard accessible.

## Data flow

UI component → API client → server validation → authorization → business logic → database

The component layer must never decide permissions, freeze a case, approve a submission, publish a response, report a review, or delete a review.

## Human-control chain

Decision → Freeze → Human Approval → Controlled Preparation/Submission

ApprovalGate explicitly communicates that approval is a human control point. It does not call an external platform and does not imply that a platform will accept or remove content.

## Initial V6.40 implementation

frontend/assets/ui-components.js contains the reusable primitives. frontend/assets/app.js remains the application orchestrator and existing API/business workflow source of truth. frontend/assets/public.css carries the shared visual layer.

## Acceptance

1. states are deterministic;
2. text is escaped before interpolation;
3. accessible semantics are present;
4. no authorization logic is in the component layer;
5. no automatic external action is performed;
6. responsive rendering is provided;
7. the contract is covered by automated tests.