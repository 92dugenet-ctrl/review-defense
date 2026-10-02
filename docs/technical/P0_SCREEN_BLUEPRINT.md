# Review Defense — P0 Screen Blueprint

## Critical screens

1. Home
2. Analysis
3. Login
4. MFA
5. Dashboard
6. Reviews
7. Analysis workspace
8. Cases
9. Case detail
10. Evidence
11. Approval
12. Settings

## Universal states

Every application screen must support:

- loading;
- populated;
- empty;
- error;
- permission denied;
- success where applicable.

## Application contract

```
UI
 ↓
API client
 ↓
Server validation
 ↓
Authorization
 ↓
Business logic
 ↓
Database
```

The frontend never authorizes sensitive actions by itself.

## Case workspace

```
Review
 ↓
Analysis
 ↓
Evidence
 ↓
Human Decision
 ↓
Freeze
 ↓
Preparation
 ↓
Approval
 ↓
Controlled Action
```

## Acceptance

A P0 screen is complete only when UI, responsive behavior, accessibility, data integration, states, permissions, analytics and tests are validated.
