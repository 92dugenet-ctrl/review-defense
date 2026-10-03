# Application — zone de transition de l'espace authentifié

## Source active

Le point d'entrée React et le routeur actifs sont dans `frontend/src/main.tsx` et `frontend/src/app/router.tsx`. Vite et TypeScript incluent `src/` et résolvent l'alias `@` vers `src/`.

Les copies strictement identiques de pages, composants, hooks, types et points d'entrée qui existaient ici ont été retirées afin d'éviter deux emplacements présentés comme sources concurrentes. Les implémentations conservées dans `src/` sont la référence actuelle.

## Contenu conservé ici

- Les README fonctionnels servent de repères de migration.
- `services/api/client.ts` est une variante historique, hors compilation React actuelle (`tsconfig.app.json` inclut uniquement `src/`). Elle diffère du client actif : elle ne lit pas le jeton partagé `readAccessToken()` et n'ajoute donc pas l'en-tête Bearer aux requêtes `/v1/`. Ne pas l'importer dans une nouvelle page ni la recopier dans `src/`.
- `dashboard/workspace.html`, `workspace.js` et `workspace.css` sont conservés comme copies historiques. Le workspace racine reste le chemin utilisé par les routes WSGI; ne pas déplacer ni supprimer ces fichiers sans vérification des références.

## Règles

- Ajouter les nouvelles pages et composants React dans `src/` tant que Vite et TypeScript y sont configurés.
- Ne pas réintroduire de copies synchronisées dans ce dossier.
- Toute future migration vers une architecture `application/` autonome doit être une opération explicite : modifier Vite/TypeScript, les imports, le routeur et les chemins de build dans un même lot vérifiable.
- Ne pas modifier les routes serveur, les ports, le WSGI ou les contrats API dans le cadre de ce nettoyage de layout.
