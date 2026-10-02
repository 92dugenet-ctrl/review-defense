# Consolidation du code — 2 octobre 2026

## Référence

- Dépôt : 92dugenet-ctrl/review-defense
- Branche de consolidation : consolidation/code-unification-20261002
- Base : develop
- Commit de départ : 23098d019558c0c2dbf10c3bfe5c9ff0edb58bfd
- Périmètre : collecte et cohérence du code uniquement. Aucun test, build, connexion au serveur, secret, déploiement ou merge vers develop/main n'est effectué dans cette phase.

## Choix de consolidation effectués

### Frontend React — pages publiques

- La version modulaire Muse de audit/muse-modular-20260930 est retenue pour les pages React publiques : HomePage, router et PricingPage.
- Les composants Muse et les pages Contact, Produit, Fonctionnement et Sécurité existaient déjà dans develop avec les mêmes contenus que cette branche ; ils sont conservés.
- Le routeur conserve un seul composant LegalPage.tsx, réutilisé par les routes légales distinctes (/mentions-legales, /confidentialite, /cookies, /cgu, /cgv, etc.).
- Les variantes concurrentes PublicPageExperiences, PublicHeader, PublicFooter et leurs feuilles de style dédiées ont été retirées de la branche de consolidation au profit du shell Muse unique.
- Le catalogue de prix Muse continue de lire le catalogue via /v1/billing/catalog et conserve l'intégration PayPal présente dans cette version.

### Frontend statique et WSGI

- wsgi.py sert toujours frontend/index.html pour / et /app, et sert les pages HTML nommées via ses routes statiques.
- L'entrée frontend/index.html a donc été conservée depuis develop. La remplacer par l'entrée Vite de chore/public-site-coherent-audit aurait laissé le serveur WSGI servir un fichier qui référence /src/main.tsx sans que le serveur ne fournisse le bundle Vite.
- La page frontend/about.html de develop est identique à la version de feat/about-editorial-muse-layout (SHA identique) : elle est conservée.
- Les pages statiques de content/front-copy-2026-09-30 sont déjà intégrées dans develop ou ont depuis été remplacées par des versions plus récentes. Aucun écrasement par cette branche n'est nécessaire.
- Les fichiers frontend/workspace.html, workspace.js et workspace.css sont déjà présents dans develop avec les mêmes SHA que la branche frontend/client-admin-workspace. La route WSGI /client et /admin dispose donc déjà de ses fichiers statiques.
- Le contrat de test de base a été conservé depuis develop afin de ne pas déclarer à tort que l'entrée WSGI statique est déjà devenue une entrée React.

### Facturation et PayPal

- La branche feature/paypal-billing-v1 n'est pas recopiée : elle est antérieure à l'architecture de facturation actuelle.
- develop possède déjà le catalogue et les services de facturation actuels, le client PayPal, ainsi que les migrations 026_v641_paypal_billing.sql, 027_v642_billing_identifier_integrity.sql et 030_v644_billing_account_state.sql.
- La migration historique 023_v70_paypal_billing.sql de cette branche entrerait en conflit avec 023_v640_session_restore.sql de develop. Les anciennes variables de configuration PayPal ont également été retirées par des commits plus récents ; elles ne sont pas réintroduites.

### Architecture de traitement

- processing-architecture-staging n'est pas recopiée : develop possède déjà migrations/029_v643_processing_architecture.sql et src/processing_jobs.py.
- Le commit « feat: complete asynchronous processing architecture » du 29 septembre est déjà représenté dans develop. La version de staging est donc une source historique, pas la version à reprendre.

### Espace client / administration

- Les fichiers de l'espace client/admin de frontend/client-admin-workspace sont déjà présents dans develop avec les mêmes SHA.
- Le téléchargement du contenu des preuves est également déjà présent dans src/api_server.py de develop. Aucune copie du backend de cette branche n'est nécessaire.

## Sources volontairement isolées

### feature/client-monitoring-hub

Cette branche a fourni une partie du travail initial du hub client/Google Business Profile. Son contenu ne devait pas être repris en bloc : la migration source `024_v641_client_monitoring_hub.sql` entrait en collision avec `024_v641_rgpd_privacy_workflow.sql` et le parcours HTTP devait être rapproché de l'API cible.

**État vérifié sur `develop` le 3 octobre 2026 :** le hub est désormais raccordé dans la cible. Les routes `GET /v1/integrations/google/start`, `GET /v1/integrations/google/callback`, `GET /v1/integrations/google/locations`, `POST /v1/integrations/google/select-location`, `GET/POST /v1/client/profile` et les routes de gestion des documents clients sont présentes dans `src/api_server.py`. Les appels correspondants sont présents dans `frontend/workspace.js`, et les méthodes de persistance sont présentes dans `src/postgres_api_repository.py`.

La migration du hub est intégrée sous le nom `migrations/031_v641_client_monitoring_hub.sql` (blob SHA `929bff81fb458c5bdfe137f2e5e5c4dae5a4cb87`). La migration source portant le numéro `024` n'est donc pas à recopier. Aucun remplacement depuis la branche source n'est requis pour ce périmètre.

### Autres branches historiques

Les branches archive/*, baseline/*, freeze/*, restore/*, ux/*, feat/v6-40-*, tmp-commercial-rebuild, feat/frontend-short-home, feat/frontend-consistent-layout, audit/public-routes-cleanup, fix/v6-40-e2e-dashboard-assertion et les branches de contenu ont été comparées à develop. Leurs apports sont soit déjà présents dans develop, soit remplacés par des versions plus récentes, soit liés à une architecture antérieure. Aucun remplacement global n'a été effectué.

## Changements effectués sur cette branche

- Sélection des versions Muse du routeur, de la page d'accueil et de la page tarifs.
- Retrait des composants et styles publics React devenus redondants avec le shell Muse.
- Conservation de l'entrée statique WSGI et de son contrat de test.
- Unification du workflow React dans .github/workflows/react-build.yml ; le workflow concurrent frontend.yml a été retiré.
- Aucun changement de develop ou main.

## À reprendre dans une phase ultérieure

- Raccorder explicitement le build React à la distribution servie par WSGI ou choisir définitivement l'architecture de frontend déployée. Le code React et le site statique coexistent encore comme deux couches ; aucune bascule de serveur n'est faite ici.
- Compléter et intégrer le hub Google Business Profile à partir de routes cohérentes et d'une migration non conflictuelle.
- Revoir les routes statiques historiques et leurs redirections une fois l'architecture frontend cible décidée.
- Compléter les champs légaux entre crochets dans LegalPage.tsx après validation des informations réelles de l'entité et de l'hébergement.

## État de validation

Aucun test automatisé, typecheck, build, test navigateur, test de connexion serveur ou déploiement n'a été lancé. Cette branche représente une consolidation de sources et une analyse statique de cohérence, pas une certification de fonctionnement.


## Inventaire des branches examinées

Les 29 références visibles ont été comparées à develop. develop est la base de cette consolidation ; main est en retard de 18 commits et n'a pas été utilisé comme base.

- Déjà intégrées ou identiques pour les fichiers concernés : audit/muse-modular-20260930, feat/about-editorial-muse-layout, content/front-copy-2026-09-30, frontend/client-admin-workspace, processing-architecture-staging.
- Sources plus anciennes ou remplacées par les fichiers actuels de develop : archive/pre-core-reset-2026-09-28, audit/public-routes-cleanup, automation/revue-defense-006, chore/public-site-coherent-audit, content/front-copy-hourly-2026-10-01, feat/frontend-consistent-layout, feat/frontend-short-home, feat/v6-40-white-blue-premium, fix/v6-40-e2e-dashboard-assertion, tmp-commercial-rebuild, ui/v6-40-premium-console, ux/v640-premium-landing.
- Fonctionnalités isolées car incomplètes ou conflictuelles : feature/client-monitoring-hub, feature/paypal-billing-v1.
- Références historiques sans apport à recopier dans cette phase : audit/phase-zero-2026-10-02, baseline/v6.40-core, certify-business-chain-run, freeze/infrastructure-v6.40, frontend-cycle-4, restore/services-before-production-refactor, restore/services-last-known-good.
- Branche de travail créée lors d'une étape précédente et volontairement non retenue : work/lot-a-foundation-20261002.
- Références de base : develop et main.

Les fichiers uniques d'une branche ancienne n'ont pas été importés uniquement parce qu'ils existaient : leur version, leur usage dans l'architecture actuelle et les dépendances associées ont été examinés avant décision.


## État consolidé du hub client / Google Business Profile — vérification du 3 octobre 2026

### Éléments présents dans `develop`

- `src/google_business_profile.py` contient les primitives OAuth/PKCE, la découverte des comptes et établissements et la lecture des avis.
- `src/postgres_api_repository.py` contient les méthodes de persistance du profil organisationnel, des documents clients, des états OAuth et des connexions Google.
- `src/api_server.py` expose les routes de démarrage et callback OAuth, de liste et sélection des établissements, de profil client et de gestion/téléchargement des documents.
- `frontend/workspace.js` appelle ces routes pour le profil, la connexion Google, la sélection d'établissement, le dépôt et le téléchargement des documents.
- La migration `migrations/031_v641_client_monitoring_hub.sql` est présente. Elle reprend le schéma de la migration source `024_v641_client_monitoring_hub.sql` avec un numéro disponible dans la séquence actuelle ; la migration `024_v641_rgpd_privacy_workflow.sql` reste distincte.

### Décision actuelle

Le hub n'est plus à classer comme une fonctionnalité HTTP manquante ou en attente de raccordement dans `develop`. Les fichiers et routes identifiés lors de la comparaison sont maintenant présents dans la branche cible. Il n'y a pas lieu de recopier la migration source numéro 024 ni de remplacer les fichiers actuels par les variantes de `feature/client-monitoring-hub`.

Cette vérification porte sur la présence et la cohérence statique des références et des routes. Elle ne constitue pas une validation de bout en bout : aucun test OAuth réel, appel Google, test de synchronisation, test de dépôt documentaire, build ou déploiement n'est revendiqué ici.

## Rapatriement effectif supplémentaire — 2 octobre 2026

### Modifications copiées sur `develop`

- Depuis `work/lot-a-foundation-20261002` :
  - `frontend/src/auth/sessionToken.ts` ajouté (blob source `633ae9fd37f82e7cd52e2bb426e3d585acb767bf`).
  - `frontend/src/services/api/client.ts` remplacé par la version qui ajoute automatiquement le jeton Bearer aux appels `/v1/` lorsqu'aucun en-tête Authorization n'est fourni (blob source `a66579be4d6dfbbc7b305f592a92ebcc1692390a`).
  - `frontend/src/auth/AuthContext.tsx` adapté pour utiliser l'accesseur partagé du jeton (blob source `748df93f2c8c71f1e38850094e0ccf3dfed5d436`).
- Depuis `chore/public-site-coherent-audit` : restauration des modules publics absents de la cible, sans les brancher aux routes actives :
  - `frontend/src/components/layout/PublicHeader.tsx`
  - `frontend/src/components/layout/PublicFooter.tsx`
  - `frontend/src/pages/PublicPageExperiences.tsx`
  - `frontend/src/styles/muse-landing.css`
  - `frontend/src/styles/public.css`
  - `frontend/src/styles/public-pages-distinct.css`
  Les SVG `visual-controls.svg`, `visual-process.svg` et `visual-workspace.svg` étaient déjà identiques dans la cible.
- Configuration : ajout dans `.env.example` des variables `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `REVIEW_DEFENSE_GOOGLE_STATE_KEY` et `REVIEW_DEFENSE_GOOGLE_TOKEN_KEY`.

### Branches examinées sans remplacement

- `frontend/client-admin-workspace` : `workspace.html`, `workspace.js`, `workspace.css`, `wsgi.py`, `src/api_server.py`, plusieurs tests, le workflow CI et les trois SVG sont déjà identiques à la cible. Les variantes des pages statiques sont plus anciennes et ne remplacent pas les versions actuelles.
- `audit/muse-modular-20260930` : composants Muse, pages et routeur contrôlés déjà identiques à la cible. Les variantes de workflow de cette branche ne remplacent pas le CI plus récent.
- `feature/paypal-billing-v1` : son client PayPal, sa migration `023_v70`, ses primitives de facturation et ses paramètres d'environnement sont issus d'une architecture plus ancienne. La cible possède déjà les modules et migrations de facturation plus récents ; aucune régression ni ancienne variable de configuration n'a été recopiée. Le document source PayPal utilise notamment un jeu de variables sandbox différent du provisionnement courant.
- `content/front-copy-hourly-2026-10-01` et `audit/phase-zero-2026-10-02` : aucun commit unique en avance sur la cible.
- `content/front-copy-2026-09-30`, `feat/about-editorial-muse-layout`, `feat/frontend-consistent-layout`, `feat/frontend-short-home`, `ui/v6-40-premium-console`, `ux/v640-premium-landing`, `frontend-cycle-4`, `restore/services-before-production-refactor`, `restore/services-last-known-good` et `archive/pre-core-reset-2026-09-28` : écarts examinés ; les versions source sont anciennes ou dépassées par les versions présentes sur `develop`. Les éléments uniques qui restent pertinents seront vérifiés à l'examen final de chaque branche avant suppression.

### Vérifications

- Les dix fichiers écrits dans cette reprise ont été relus sur `develop` et leurs empreintes confirmées.
- Les trois fichiers de traitement asynchrone précédemment copiés restent présents sur `develop`.
- Les tests et le build frontend n'ont pas encore été exécutés ; aucune validation verte n'est revendiquée.
- `main` n'a pas été modifiée. Aucune branche secondaire n'a été supprimée.
