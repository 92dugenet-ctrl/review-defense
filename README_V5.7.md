# Review Defense V5.7 — Google Business Profile Integration Layer

V5.7 adds a framework-neutral, read-oriented Google Business Profile integration boundary.

## Implemented

- OAuth 2.0 authorization URL with `business.manage` scope, signed short-lived `state`, and PKCE S256.
- Authorization-code exchange and refresh-token handling.
- Tenant-scoped token store reference adapter.
- Google Account Management API account discovery.
- Business Information API location discovery.
- Business Profile Reviews API review listing and retrieval.
- Pagination support for accounts, locations and reviews.
- Normalization into the existing `ReviewContext` contract.
- Tenant-scoped observed review cache with `NEW`, `UPDATED`, and `UNCHANGED` detection.
- Explicit handling of API errors without exposing access tokens.
- Strict resource-path validation.
- Injectable HTTP transport for deterministic integration tests.
- Explicit mutation boundary: V5.7 does **not** automatically report, delete, or reply to reviews.

## Official Google boundaries

Google requires OAuth 2.0 authorization for Business Profile API requests. The current documented scope is `https://www.googleapis.com/auth/business.manage`.

Account discovery uses the Account Management API, location discovery uses the Business Information API, and review retrieval uses the Reviews API. Google documents no sandbox for these APIs, so the test suite uses an injected fake transport rather than making live calls.

The Review Defense product remains human-approval driven: synchronizing a review is not a decision that the review violates policy, and no removal probability is calculated.

## Production requirements

Before live deployment, configure an approved Google Cloud project, OAuth consent screen, credentials, redirect URIs and required Business Profile API access. Store refresh tokens only in encrypted server-side secret storage/KMS, use TLS, rotate credentials, record consent/revocation events, enforce tenant binding, and apply Google's quotas and policies.

No live Google credential is included in this repository.
