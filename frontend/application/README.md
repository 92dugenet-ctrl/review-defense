# Application — espace authentifié cible

## Responsabilité

Organiser l'espace applicatif par fonctionnalité : tableau de bord, avis, dossiers, analyse, documents, facturation, paramètres et notifications.

## Structure présente

- `main.tsx`, `app/router.tsx` : démarrage et déclaration des routes.
- `components/` : shell applicatif et composants UI.
- `dashboard/` : tableau de bord, notifications et fichiers historiques associés.
- `reviews/`, `cases/`, `analysis/` : vues métier.
- `billing/`, `documents/`, `settings/` : facturation, documents et paramètres.
- `hooks/`, `services/`, `types/` : appels API, hooks et contrats TypeScript.

## Point d'attention important

Ce dossier n'est pas actuellement autonome. Le `vite.config.ts` définit l'alias `@` vers `./src`. Les imports de `application/main.tsx` et `application/app/router.tsx` résolvent donc plusieurs dépendances depuis `src/` (styles, pages, auth et composants). Les pages de `application/` sont organisées par dossiers fonctionnels, tandis que le routeur inspecté importe les pages via `@/pages/*`.

Il existe aussi des fichiers workspace HTML/JS/CSS sous `application/dashboard/`; leur présence ne prouve pas qu'ils sont servis par WSGI.

## Règles de migration

- Ne pas considérer `application/` comme point d'entrée actif tant que Vite, TypeScript et le serveur ne le référencent pas explicitement.
- Définir un propriétaire unique pour chaque page et composant avant de supprimer les doublons dans `src/`.
- Conserver les contrats API, permissions serveur, URL et comportements existants.
- Ne pas déplacer le workspace historique dans ce dossier sans mise à jour contrôlée des routes serveur et des chemins d'assets.
