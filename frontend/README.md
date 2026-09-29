# Review Defense Frontend

New frontend foundation for Review Defense.

## Stack

- React
- TypeScript
- Vite
- React Router

## Structure

- `src/components` — reusable UI and layout
- `src/pages` — route-level screens
- `src/services` — backend/API integration
- `src/hooks` — reusable React logic
- `src/types` — shared frontend contracts
- `src/styles` — design tokens and global styles

The frontend is intentionally independent from the previous static frontend implementation. The existing backend API remains the source of truth for HTTP contracts.

## Commands

```bash
npm install
npm run typecheck
npm run build
npm run dev
```
