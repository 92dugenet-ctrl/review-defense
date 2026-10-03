# Cartographie des styles React

## Entrées globales

Le point d'entrée `src/main.tsx` importe explicitement :
- `tokens.css` : variables de thème, typographie et dimensions globales ;
- `global.css` : reset, shell de l'espace connecté, authentification et composants d'interface communs.

Ces deux feuilles constituent la base du bundle React. Ne pas les retirer ni les remplacer par les fichiers de `public/styles/` sans migration vérifiée.

## Feuilles spécialisées

Les feuilles suivantes appartiennent au système de pages/composants React. Vérifier leurs imports dans les composants concernés avant toute modification :
- `muse-landing.css` : identité et sections de la page d'accueil `.rd-home` ;
- `muse-v3.css` : scènes et composants de l'expérience Muse ;
- `public.css` : habillage public partagé, en-tête, pied de page, contact et tarifs ;
- `public-secondary.css` : système de pages publiques secondaires ;
- `public-pages-distinct.css` : styles dédiés aux pages produit, fonctionnement et sécurité.

Une feuille peut être chargée depuis un composant plutôt que depuis `main.tsx`. L'absence d'import dans le point d'entrée ne prouve donc pas qu'elle est inutilisée.

## Frontières à préserver

- `frontend/assets/*.css` : ressources statiques servies par le runtime WSGI ; conserver leurs chemins.
- `frontend/workspace.css` : feuille du workspace historique, chargée par `workspace.html`.
- `frontend/styles.css` : feuille chargée par `frontend/index.html` et `workspace.html` via `/styles.css`.
- `frontend/assets/premium-console-v640.css` : chargée directement par `workspace.html`.
- `frontend/dist/assets/*.css` : artefacts générés par Vite ; ne pas éditer à la main.
- `frontend/style.css` : feuille historique distincte ; ne pas confondre avec `frontend/styles.css`.
- `frontend/public/styles/*.css` : ressources de transition/historiques ; leur présence ne signifie pas qu'elles sont intégrées au bundle React.

## Copies identiques observées

Au commit de cette cartographie, les empreintes Git confirment les paires identiques suivantes :
- `public/styles/global.css` = `src/styles/global.css`
- `public/styles/muse-v3.css` = `src/styles/muse-v3.css`
- `public/styles/public-secondary.css` = `src/styles/public-secondary.css`
- `public/styles/tokens.css` = `src/styles/tokens.css`
- `public/styles/style.css` = `frontend/style.css`

Ces fichiers ne sont pas supprimés : les copies historiques peuvent être référencées par du HTML statique, des liens directs ou des outils de publication. Avant dédoublonnage, rechercher les références URL/HTML et confirmer les chemins servis en production.

## Règle de modification

Toute suppression ou fusion doit établir les imports React, les références HTML, les URLs servies par WSGI et la sortie de build. Ne pas déduire l'inutilité d'une feuille de son seul nom, de son emplacement ou de son ancienneté.
