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

## Vérification des chargements (commit 89aab5d)

### React

Chargements directs confirmés :
- `src/main.tsx` importe `src/styles/tokens.css` et `src/styles/global.css`.
- `src/components/public/muse/MuseShell.tsx` importe `src/styles/muse-v3.css`. Les pages React publiques actives qui utilisent `MuseShell` héritent donc de cette feuille.
- `src/pages/MusePublicPage.tsx` importe également `muse-v3.css` ; cette page est une variante historique et n'est pas la page d'accueil active du routeur.
- Les variantes `PublicProductPage`, `PublicMethodPage`, `PublicSecurityPage`, `PublicPricingPage` importent `public-secondary.css` ; `PublicPageExperiences` importe `public-pages-distinct.css`. Elles ne sont pas les pages actuellement associées aux routes publiques principales du routeur.

Les pages publiques actives actuelles (`HomePage`, `ProductPage`, `MethodPage`, `SecurityPage`, `PricingPage`, `ContactPage`) utilisent le shell Muse. Aucun import direct de `muse-landing.css` ou `src/styles/public.css` n'a été trouvé dans les points d'entrée et composants de route examinés. Cela ne suffit pas à autoriser leur suppression : les imports indirects et les usages non-React doivent encore être contrôlés.

### HTML historique / runtime statique

Chargements HTML confirmés :
- `frontend/workspace.html` : `/styles.css`, `/workspace.css`, `/assets/premium-console-v640.css?v=6401`, puis `/workspace.js`.
- `frontend/index.html` : `styles.css` et `script.js`.
- `frontend/services.html` : `/styles.css` et `/script.js`.
- `frontend/landing.html` : `/assets/public.css?v=6711` et `/assets/public.js?v=6711`.
- `frontend/public/pages/index.html` : `styles.css` et `script.js`.
- `frontend/application/dashboard/workspace.html` : `/styles.css` et `/workspace.css`.

Ces liens confirment que plusieurs feuilles hors de `src/styles/` restent nécessaires à des pages HTML historiques. Ne pas supprimer ou déplacer `frontend/styles.css`, `frontend/workspace.css`, `frontend/assets/premium-console-v640.css`, `frontend/assets/public.css` ou `frontend/public/styles/styles.css` dans cette étape.

### Limites de l'audit

La vérification a couvert le point d'entrée React, les pages du routeur, les composants de shell Muse et les principales pages HTML identifiées dans l'arbre. Elle ne constitue pas encore une analyse d'exécution navigateur ni une preuve que les feuilles non directement importées sont sans usage. Aucun CSS n'est supprimé dans cette étape.
