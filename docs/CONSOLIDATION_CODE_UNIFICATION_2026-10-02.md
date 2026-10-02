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

Cette branche contient une tentative de hub client/Google Business Profile, mais son ensemble n'est pas cohérent à reprendre tel quel :

- Son interface appelle notamment /v1/integrations/google/start, /locations, /select-location, /v1/client/profile et /v1/client/documents.
- Son src/api_server.py expose un callback OAuth et des helpers, mais ne fournit pas l'ensemble des routes attendues par l'interface.
- Sa migration 024_v641_client_monitoring_hub.sql entre en collision avec la migration 024_v641_rgpd_privacy_workflow.sql déjà présente dans develop.
- Des méthodes de persistance liées aux profils, documents et connexions Google existent déjà dans src/postgres_api_repository.py de develop, mais cela ne rend pas le parcours HTTP de cette branche complet.

Le hub est donc conservé comme source à reprendre ultérieurement par intégration sélective, avec renumérotation de migration et rapprochement des routes. Aucun faux raccordement n'est ajouté dans cette phase.

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
