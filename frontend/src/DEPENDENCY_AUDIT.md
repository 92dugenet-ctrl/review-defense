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
## Contrôle des contrats API — audit React/backend

Comparaison statique de `src/api_server.py` avec les appels émis par les pages routées.

- `ReviewsPage` : `GET /v1/reviews` renvoie `items`; les champs affichés correspondent au modèle Review. Contrat cohérent.
- `ReviewDetailPage` : `GET /v1/reviews/{id}` renvoie `review` et `policy_signals`; `POST /v1/cases` attend `review_id` et renvoie `case.case_id`. Contrat cohérent.
- `CasesPage` : `GET /v1/cases` renvoie `items` de cas avec `case_id`, `status` et `created_at`. Contrat cohérent.
- `CaseDetailPage` : le workspace est enveloppé sous `workspace`; l'avis est `workspace.review`, les preuves sont `workspace.evidence` et les besoins complémentaires sont `evidence_tasks`. L'ancienne page lisait les propriétés au mauvais niveau. Corrigé pour consommer le contrat réel.
- `AnalysisPage` : `GET /v1/review-queue` et `/workload` renvoient respectivement `items` et un objet contenant `items`; le composant consomme la file et le champ `total` de workload, mais le backend expose `items`/`count` et des métriques par utilisateur. Le total affiché doit donc être calculé à partir de `items` si l'on souhaite une charge agrégée. (À traiter dans l'étape suivante après vérification des champs de charge.)
- `BillingPage` : `GET /v1/billing` expose `account`, `events`, `paypal_configured`; `/billing/catalog` expose `items` et les offres `kind=subscription`; les routes PayPal de configuration et confirmation correspondent aux appels de la page.
- `AdminPage` : `GET /v1/organization/invitations` n'existe pas côté API ; seul `POST /v1/organization/invitations` est déclaré. Le changement de rôle est `POST /v1/organization/members/{user_id}/role`, pas PATCH. Le frontend a été corrigé : chargement des membres seul, affichage explicite de la dernière invitation créée sans prétendre lister toutes les invitations, et méthode POST pour les rôles.
- `AdminPage` : `POST /v1/auth/revoke-all` cible l'utilisateur courant par défaut. Le bouton a été renommé pour préciser l'effet et la page déconnecte l'utilisateur après révocation.
- `NotificationsPage` : `GET /v1/notifications` et POST `/{id}/deliver`/`/{id}/cancel` existent. Le backend réserve la lecture aux rôles OWNER/ADMIN/ANALYST et les actions aux OWNER/ADMIN ; l'interface ne doit pas être interprétée comme une autorisation.
- `PrivacyPage` : GET export et GET/POST requests existent. La liste utilise `id`, `request_type`, `status`, `due_at`, `created_at`; la création renvoie `{request: row}`. L'export est un objet JSON et le frontend le télécharge en JSON.

Limites : audit statique des contrats déclarés dans `src/api_server.py`, pas d'appel HTTP sur serveur réel. Les autorisations effectives restent celles du backend. Les contrôles d'organisation et d'UUID ne sont pas modifiés ici.