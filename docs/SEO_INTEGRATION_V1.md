# Review Defense — SEO Integration V1

## Runtime

The SEO runtime is already implemented through:

- `src/seo_content.py`
- `src/seo_renderer.py`
- `frontend/assets/seo.css`

The page index contains the SEO pack's editorial and commercial URL inventory.

## Commercial conversion point

`/analyse-avis-google/` is the central conversion page.

Primary CTA:

**Analyser un avis**

## Editorial clusters

- Suppression d'avis Google
- Faux avis
- Signalement
- Refus / appel
- Cas particuliers
- Services

## Internal linking rule

Each article should connect to:

- its parent hub;
- relevant neighboring articles;
- a procedural page;
- `/analyse-avis-google/`;
- the pillar when relevant.

## Canonical consolidation

The following duplicate families must not be indexed as independent equivalents:

- `google-refuse-de-supprimer-mon-faux-avis-que-faire`
- `google-refuse-de-supprimer-mon-faux-avis`
- `pourquoi-mon-avis-google-reste-en-ligne`
- `pourquoi-mon-avis-google-reste-en-ligne-conversationnel`
- `avis-google-accusation-mensongere` duplicate variants
- `avis-google-argent-ou-avantage`
- `avis-google-argent-avantage`

The runtime should keep one canonical intent and avoid pushing duplicate URLs through internal links.

## Technical SEO

Required:

- self canonical on indexable pages;
- noindex/private treatment for application routes;
- sitemap containing canonical indexable pages;
- robots disallowing private/API routes;
- Article/Service/Breadcrumb/FAQ structured data only when supported by visible content;
- page-specific metadata rather than generic descriptions where possible.

## Product positioning

SEO content must not claim:

- guaranteed removal;
- automatic reporting;
- automatic response;
- automatic Google action.

The product prepares and structures information; the final external decision remains controlled and explicit.
