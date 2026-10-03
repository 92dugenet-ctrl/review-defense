# Frontend — carte de l'interface

Le frontend contient plusieurs générations d'interface qui coexistent. Les dossiers ne sont pas interchangeables : certains sont actifs dans le runtime actuel, d'autres servent de cible de migration ou de copies de transition.

## Carte rapide

| Zone | Rôle | État |
|---|---|---|
| `public/` | Composants React et pages du site public | Structure cible; les copies publiques historiques restent servies |
| `auth/` | Contexte et garde d'authentification React, écrans de connexion/inscription | Modules React organisés; vérifier le point d'entrée qui les consomme |
| `application/` | Organisation cible de l'espace applicatif par fonctionnalité | En cours; plusieurs fichiers s'appuient encore sur l'alias `@` vers `src/` |
| `src/` | Source React actuellement référencée par Vite | Entrée React configurée dans le build Vite |
| `assets/` | JS/CSS, images, vidéos et assets statiques historiques | Répertoire statique utilisé par le WSGI actuel |
| `workspace.html/js/css` | Workspace historique client/admin | Toujours servi sur les routes d'espace connues |
| `dist/` | Résultat compilé de Vite | Artefacts générés; ne pas modifier manuellement |

## Chemins réellement utilisés

### Site public et workspace historique

- Le WSGI sert le site public depuis `src/seo_site.py`.
- Les ressources statiques historiques sont servies depuis `frontend/assets/`.
- `workspace.html`, `workspace.js` et `workspace.css` constituent encore le workspace servi par les routes d'espace.
- Les chemins historiques ne doivent pas être supprimés ou déplacés tant que le serveur et les routes n'ont pas été migrés et vérifiés.

### Build React

- Le projet Node est défini dans `package.json`.
- Vite utilise `frontend/index.html` comme entrée legacy et `frontend/src/main.tsx` comme entrée React.
- L'alias TypeScript/Vite `@` pointe actuellement vers `frontend/src/`.
- `npm run build` exécute TypeScript puis Vite; `npm run typecheck` lance le contrôle TypeScript.

## Attention aux doublons

`src/` et `application/` contiennent des fichiers de démarrage et de routage portant les mêmes noms et, pour les points inspectés, les mêmes contenus. Cependant, l'alias `@` de Vite pointe vers `src/`. Les fichiers de `application/` ne constituent donc pas une application autonome : leurs imports peuvent résoudre vers `src/pages`, `src/styles`, `src/auth` et `src/components`.

`public/` et `src/components/public/` comportent également des composants de site public en parallèle. `public/MIGRATION.md` précise que les fichiers de ce dossier sont des copies de transition des pages et assets historiques. Ne pas synchroniser ni supprimer ces copies à l'aveugle.

## Règles de maintenance

1. Identifier le consommateur et le point d'entrée avant de modifier un fichier.
2. Ne pas confondre source React, copie de transition et artefact `dist/`.
3. Préserver les URL publiques, les routes d'espace, les contrats `/v1` et les noms d'assets consommés par le WSGI.
4. Garder l'authentification et les permissions effectives côté backend; les gardes frontend ne sont pas une frontière de sécurité.
5. Ne déplacer ni renommer des fichiers avant d'avoir vérifié les imports, alias, références HTML/CSS/JS, routes serveur et scripts de build.
6. Migrer un périmètre à la fois et conserver une compatibilité pendant la transition.

## Prochaine migration

La cible est une séparation nette entre `public/`, `auth/` et `application/`, avec un seul point d'entrée React explicite. Cette séparation devra être réalisée par étapes après comparaison des composants et pages, définition des routes finales et vérification du raccordement serveur. Cette documentation ne bascule aucun chemin de production.
