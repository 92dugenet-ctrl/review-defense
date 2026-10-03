# Audit de dépendances frontend — état actuel de develop

> Audit actualisé au lot K. Pour les modules parallèles, duplications et décisions de maintenance, voir [l'audit transversal](../../docs/technical/UNUSED_AND_REDUNDANT_MODULES_AUDIT.md).

## Entrées

- `frontend/react.html` fournit `#root` et charge `src/main.tsx`.
- `src/main.tsx` monte `AuthProvider` et `RouterProvider`, puis charge les styles globaux.
- `frontend/index.html` est le site HTML historique, distinct du shell React.
- `vite.config.ts` déclare les deux documents comme entrées et configure la base `/react/`.
- Le WSGI sert la racine depuis `frontend/index.html`, les pages SEO depuis `src.seo_site` et certains chemins applicatifs via `workspace.html`. La présence du routeur React ne signifie pas que toutes les URLs de production lui sont transférées.

## Routes React

Le routeur est `src/app/router.tsx`. Il déclare les pages marketing (`/`, `/produit`, `/fonctionnement`, `/securite`, `/tarifs`, `/contact`), les pages légales, `/login`, `/register`, puis l'espace protégé `/app/*` : dashboard, avis, dossiers, analyse, notifications, facturation, paramètres, confidentialité et administration. Une route de repli affiche `NotFoundPage`.

## Graphe des composants

- `HomePage` compose `MuseShell` et `HomeBlocks`.
- `MuseShell` fournit en-tête, pied de page, styles Muse et hook de mouvement.
- Les pages marketing spécialisées composent leurs sections dans `components/public/muse/`.
- `AppShell` encadre les pages protégées.
- `AuthContext` et `RequireAuth` gèrent l'état de session et la garde de navigation.
- Les pages utilisent le client HTTP partagé `services/api/client.ts`.

Un composant non déclaré directement dans le routeur peut être un enfant, layout, hook, type ou service. Il ne doit pas être classé orphelin sur cette seule base.

## Assets et parcours historiques

- Le WSGI sert les URLs `/assets/*` depuis `frontend/assets/`.
- Vite utilise `frontend/public/` comme répertoire public de l'application compilée.
- Les deux arbres d'assets partagent 62 blobs identiques, mais ont aussi des fichiers spécifiques et un README divergent.
- Les pages et scripts historiques restent distincts du graphe React.

## Décision

Aucun composant, style, asset, route ou page n'est supprimé dans cet audit. Les candidats et les vérifications nécessaires sont détaillés dans l'audit transversal du lot K.

Aucun build, typecheck, test navigateur ou test automatisé n'a été exécuté.
