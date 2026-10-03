# Public asset and legacy-page migration

This directory retains historical public-site assets, static HTML pages, stylesheets, and a small number of React components that are not exact duplicates of the active source.

## Active React source

The configured React entry is `src/main.tsx`, with routing in `src/app/router.tsx`. Public pages live in `src/pages/`, reusable public components in `src/components/public/`, and active React styles in `src/styles/`.

The byte-identical React copies formerly under `public/components/` and `public/pages/` have been removed. This avoids maintaining two identical source trees.

## Preserved migration material

- Static pages copied from legacy frontend locations remain under `pages/*.html`.
- Historical media and scripts remain under `assets/`.
- Legacy stylesheets remain under `styles/`.
- Non-identical React components remain pending review; do not treat them as active entry points without checking imports and routing.

Do not delete or relocate legacy assets/pages until their URL references, server routing, and browser parity have been verified.
