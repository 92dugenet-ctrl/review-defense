# Audit de cohérence — dépendances frontend

## Entrées et frontière de rendu

- `frontend/vite.config.ts` déclare deux entrées de build : `index.html` (nommée `legacy`) et `src/main.tsx` (nommée `react`).
- `frontend/index.html` est une page HTML historique : elle ne contient pas d'élément `#root` et ne charge pas `src/main.tsx`. Elle charge `script.js` et `styles.css`.
- `src/main.tsx` monte le routeur React dans `#root`, importe `tokens.css` et `global.css`, puis installe `AuthProvider`.
- Le routeur React est défini uniquement dans `src/app/router.tsx`. Le runtime WSGI continue de servir la racine via `src/seo_site.py` et l'ancien workspace via `workspace.html` ; le build Vite n'est pas, à lui seul, un basculement du site en production.

Conséquence : ne pas supprimer `index.html`, `script.js`, `styles.css`, `workspace.html`, `workspace.js` ou les routes statiques historiques lors du nettoyage du graphe React.

## Graphe React actif

- `main.tsx` → `AuthContext` + `app/router.tsx`.
- `router.tsx` → pages publiques, pages légales, authentification, `RequireAuth`, `AppShell` et pages de l'espace connecté.
- Les six pages marketing actives utilisent `MuseShell` et leurs sections modulaires dans `components/public/muse/`.
- `MuseShell` importe `styles/muse-v3.css` et utilise `components/public/muse/useMuseMotion.ts`.
- `HomePage` utilise `HomeBlocks`, qui compose les sections de l'accueil.
- Les pages de compte et de l'espace connecté utilisent le client API canonique `services/api/client.ts`.

## Variantes historiques — conservées volontairement

- `MusePublicPage.tsx` est une ancienne page monolithique et utilise l'ancien hook `components/public/MuseMotion.tsx`. Ce hook ne doit pas être confondu avec `components/public/muse/useMuseMotion.ts`, qui est utilisé par le shell actif.
- `PublicPageExperiences.tsx` et `PricingPagePayPal.tsx` utilisent `components/layout/PublicHeader.tsx` et `PublicFooter.tsx`. Ces composants ne sont donc pas des fichiers orphelins même s'ils ne sont pas importés par les routes actuelles.
- `PublicProductPage.tsx`, `PublicMethodPage.tsx`, `PublicSecurityPage.tsx`, `PublicPricingPage.tsx` et `PublicContactPage.tsx` restent des variantes non raccordées au routeur.
- `PricingPagePayPal.tsx` importe `styles/public.css`; il s'agit d'une dépendance de la variante tarifaire historique. Le parcours tarifaire actif est `PricingPage.tsx`.

## Candidats à une décision ultérieure — aucune suppression

- `hooks/useApi.ts` n'est pas importé par les pages examinées ; il délègue néanmoins au client API canonique. Avant suppression, faire une recherche complète sur tous les consommateurs et décider si ce hook doit rester une API interne réutilisable.
- `components/ui/Button.tsx` n'apparaît pas dans les imports des pages routées examinées. Ne pas supprimer sans une recherche exhaustive des imports dans tous les dossiers et variantes.
- `styles/muse-landing.css` ne présente pas d'import direct dans les pages et composants actifs examinés. Ne pas supprimer avant contrôle des imports indirects, des classes CSS utilisées et des HTML statiques.
- `PublicHeader` et `PublicFooter` sont utilisés par les variantes historiques mentionnées ci-dessus : conserver tant que ces variantes sont gardées.

## Routes et assets vérifiés

- Les liens internes extraits des principales sections Muse examinées pointent vers des routes React existantes : `/register`, `/login`, `/produit`, `/fonctionnement`, `/securite` et `/tarifs`.
- Les références locales `/visual-workspace.svg` et `/visual-process.svg` existent sous `frontend/public/` et sont donc cohérentes avec les chemins publics Vite.
- `frontend/index.html` contient des liens historiques tels que `/services`, `/resources`, `/about`, `/tarif` et `/analyse-avis-google/`. Ils ne figurent pas dans le routeur React ; ne pas les réécrire automatiquement, car la page et ses URLs appartiennent au parcours HTML/SEO historique.

## Décisions de maintenance

- Aucun fichier source, composant, route, style ou asset n'est supprimé dans cet audit.
- Toute suppression ultérieure doit être précédée d'une recherche de références dans l'ensemble du dépôt, y compris HTML, CSS, JavaScript statique, tests, scripts et configuration.
- Les routes et contrats API sont hors périmètre de cet audit documentaire.
- Cette cartographie ne remplace pas un `typecheck`, un build Vite, ni un test de navigation dans un navigateur.

## État de validation

Audit statique des fichiers et références GitHub effectué. Aucun build, typecheck ou test navigateur n'a été exécuté dans cette étape.