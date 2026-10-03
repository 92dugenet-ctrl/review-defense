# Cartographie de consolidation du frontend — 2026-10-03

## Objectif

Définir une source de vérité lisible pour le frontend sans modifier le comportement, les routes HTTP, les ports, le serveur WSGI ou les contrats API. Cette cartographie est basée sur l'arbre Git de `develop` au commit `b906d0f5366b3dce300366801679dc63efd5861a`.

## Décision de structure

| Zone | Décision actuelle | Motif |
|---|---|---|
| `frontend/src/` | Source React de référence à court terme | Vite et TypeScript pointent explicitement vers ce dossier. |
| `frontend/application/` | Dossier de migration à résorber progressivement | Il contient des copies de fichiers de `src/`, mais n'est pas autonome : l'alias `@` résout vers `src/`. |
| `frontend/public/` | Copie de transition du site public et de ses médias | `public/MIGRATION.md` indique explicitement que les fichiers sont des copies d'anciens emplacements. |
| `frontend/auth/` | Copie/organisation de transition à comparer | Des fichiers équivalents existent dans `src/auth/`; le contexte d'authentification diffère. |
| `frontend/assets/` | Chemin historique à préserver | Le WSGI actuel sert les assets statiques depuis ce répertoire. |
| `frontend/workspace.html/js/css` | Workspace historique à préserver | Ces fichiers restent associés aux routes d'espace servies par le WSGI. |
| `frontend/dist/` | Sortie générée | Ne pas éditer manuellement. |

## Preuves de configuration

- `frontend/vite.config.ts` définit l'alias `@` vers `./src`.
- Vite déclare deux entrées de build : `frontend/index.html` (legacy) et `frontend/src/main.tsx` (React).
- `frontend/tsconfig.app.json` limite l'inclusion à `src` et mappe également `@/*` vers `src/*`.
- `frontend/src/main.tsx` monte le routeur depuis `src/app/router.tsx`.
- Le routeur React actif importe les pages depuis `@/pages/*`, donc depuis `src/pages/*`.
- La documentation WSGI du dépôt identifie toujours les pages publiques et le workspace historiques comme chemins servis en production. Le build Vite ne constitue pas à lui seul une bascule du serveur.

## Doublons strictement identiques observés

Les SHA Git des fichiers montrent des copies octet pour octet, pas seulement des fichiers qui portent le même nom.

### `application/` vers `src/`

Les fichiers suivants ont le même SHA dans les deux emplacements :

- `main.tsx` et `app/router.tsx`.
- Pages `AnalysisPage`, `BillingPage`, `CaseDetailPage`, `CasesPage`, `DashboardPage`, `NotFoundPage`, `NotificationsPage`, `ReviewDetailPage`, `ReviewsPage` et `SettingsPage).
- `AppShell.tsx`, `Button.tsx`, `useApi.ts`, `types/api.ts` et `vite-env.d.ts`.

Attention : cette égalité ne rend pas `application/` autonome. Les imports avec `@` sont résolus vers `src/`. Le client API n'est en revanche pas identique : `src/services/api/client.ts` ajoute l'injection centralisée du bearer token et diffère de `application/services/api/client.ts`.

### `public/` vers `src/`

Plusieurs dizaines de composants/pages/styles publics ont le même SHA dans les deux emplacements, notamment :

- Les composants Muse (home, product, method, pricing, security et contact).
- Les composants de navigation publique et les pages Contact, Home, Legal, Method, MusePublic, Pricing, Privacy, Product, PublicContact, PublicMethod, PublicPricing, PublicProduct, PublicSecurity et Security.
- Les feuilles `global.css`, `muse-v3.css`, `public-secondary.css` et `tokens.css`.

La copie sous `public/` n'est pas le point d'entrée React sélectionné par Vite. Son dossier `assets/` contient aussi des médias et des ressources statiques de transition : ne pas confondre ces fichiers avec les composants compilés sous `src/`.

## Doublons qui ne doivent pas être fusionnés automatiquement

- `frontend/auth/AuthContext.tsx` et `frontend/src/auth/AuthContext.tsx` sont différents. La version `src` utilise `auth/sessionToken.ts` et `readAccessToken`; l'autre lit directement une clé de session. Garder la version réellement consommée par `src/main.tsx` comme référence et examiner les appels externes avant suppression de l'autre.
- `frontend/application/services/api/client.ts` et `frontend/src/services/api/client.ts` sont différents. La version `src` ajoute l'authentification bearer centralisée et un traitement d'en-têtes plus robuste. Ne pas remplacer l'une par l'autre sans analyse des consommateurs.
- Les fichiers `workspace.html/js/css` de `frontend/application/dashboard/` ne sont pas les fichiers racines servis par les routes historiques. Leur présence ne justifie aucun déplacement ou remplacement.

## Ordre de consolidation recommandé

1. Conserver `src/` comme source React unique pendant la migration.
2. Rechercher les imports/références réels de chaque fichier `application/` et `public/` avant toute suppression. Les doublons exacts peuvent être retirés uniquement après confirmation qu'aucun outil, script ou chemin de build ne les consomme directement.
3. Comparer explicitement les versions divergentes du client API et du contexte d'authentification; choisir une implémentation canonique et mettre à jour les imports dans une opération distincte.
4. Vérifier les références des pages et médias historiques, les routes WSGI, les URL SEO et les chemins d'assets avant toute suppression des copies `public/`.
5. Ne migrer le workspace historique qu'après validation du routage serveur et de la parité fonctionnelle du nouvel espace React.
6. Après chaque lot de déplacement/suppression : typecheck, build Vite, vérification des routes publiques et protégées, puis contrôle des chemins d'assets.

## Périmètre de ce commit

Ce commit ajoute uniquement cette cartographie. Aucun fichier applicatif, asset, route, configuration Vite/TypeScript, serveur, port ou contrat API n'est modifié. Aucun workflow GitHub ni pull request n'est créé.
