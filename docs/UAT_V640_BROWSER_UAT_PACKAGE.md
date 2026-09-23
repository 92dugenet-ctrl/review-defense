# V6.40 Browser UAT package

This package binds the UAT scenarios to the existing browser runners and the review-to-case flow.

## Required browser assertions
- login form is present before fill/click;
- MFA challenge appears when enforced;
- dashboard renders;
- Reviews renders;
- **Créer le dossier** is present for an authorized user;
- POST `/v1/cases` contains the review ID;
- created case appears in Dossiers;
- no direct Google resource is loaded;
- no automatic Google submission occurs.

## Runners
- `scripts/browser_e2e.py` — basic browser contract.
- `scripts/staging_e2e.py` — live HTTPS + MFA + browser certification.
