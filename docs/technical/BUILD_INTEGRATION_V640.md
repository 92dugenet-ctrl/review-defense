# Review Defense — V6.40 Construction Integration

## Source of truth

The repository already contains the V6.40 production application, authentication/MFA, multi-tenant API, evidence/case workflow, SEO renderer and CI certification pipeline. This integration adds the agreed construction specification without replacing the existing architecture.

## Implemented in this commit

- Premium public navigation aligned with the construction blueprint.
- Primary public CTA standardized to **Analyser un avis**.
- Homepage positioning aligned to **Analyse → Préparation → Contrôle humain**.
- Pricing model aligned to Monitoring / Professional / Business / Enterprise.
- Services section added to the public marketing shell.
- Premium design tokens layered into the existing public stylesheet.
- Construction documentation stored with the repository.
- SEO corpus remains driven by `src/seo_content.py` and the existing server-rendered SEO layer.

## Architecture

```
MARKETING
  /
  ?page=features
  ?page=how
  ?page=services
  ?page=pricing
  ?page=resources
  /analyse-avis-google/

SEO
  /suppression-avis-google/
  /faux-avis-google/
  /signaler-un-avis-google/
  /que-faire-quand-google-refuse-de-supprimer-un-avis/
  + specialized pages from src/seo_content.py

APPLICATION
  /app
  /v1/*
```

## Safety workflow

```
Analysis
  ↓
Decision
  ↓
Freeze
  ↓
Human Approval
  ↓
Controlled Preparation
  ↓
Controlled Submission
```

No automatic Google deletion, reporting or response is introduced by this integration.

## Validation target

The existing GitHub Actions workflow must remain green for:

1. Python compilation
2. Full pytest regression
3. Release contract
4. GitHub staging contract
5. Deployment preflight
6. Repository-only certification
7. PostgreSQL/RLS certification
8. Business-chain certification
9. UAT package certification
10. Optional live staging and browser E2E when secrets are configured

## Important

This commit deliberately reuses the existing V6.40 monolithic frontend/API architecture. It does not introduce a parallel React application or duplicate backend. The goal is to stabilize and commercialize the existing product rather than trigger an architectural rewrite.
