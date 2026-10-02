# Public asset and legacy-page migration

This directory contains byte-for-byte copies of the existing public-site assets and static pages, placed under the target public frontend structure.

- Original files remain at their legacy paths during the migration.
- Assets are copied from `frontend/assets/` into this directory with their relative subdirectories preserved.
- Static pages from `frontend/` and `frontend/resources/` are copied into `pages/`.
- The legacy public JavaScript entry is copied to `assets/js/public.js`.
- Both legacy stylesheets are preserved under `styles/`.

These are archival/transition copies. Update relative asset URLs and routing before switching production serving to these new paths; do not delete the legacy originals until browser E2E tests confirm parity.
