# Cartographie technique exhaustive — Review Defense

> Cartographie générée depuis l'arbre Git de `develop`. Elle décrit les fichiers présents et les points d'entrée vérifiés par lecture du code ; la présence d'un fichier ne prouve pas qu'il est importé en production.

## 1. Périmètre observé

- Branche examinée : `develop`.
- Fichiers suivis dans l'arbre Git : **824**.
- Sources Python : **304** (ce total inclut scripts, tests et modules).
- Sources frontend JS/TS : **100**.
- Fichiers SQL : **65**.

## 2. Chaîne d'exécution vérifiée

```text
Dockerfile / Compose
  └─ scripts/start_production.sh
       ├─ scripts/production_check.py
       ├─ scripts/migrate.py → migrations/*.sql
       └─ Gunicorn → wsgi.py
            ├─ src.seo_site (rendu public SEO)
            └─ src.api_server.create_app (API /v1)
                 └─ services src/* + repositories PostgreSQL
```

Le point d'entrée WSGI importe explicitement `src.api_server.create_app`. Il sert aussi les ressources et routes frontend historiques et délègue le rendu SEO à `src.seo_site`. Le README du dépôt identifie `frontend/src/main.tsx` et `frontend/src/app/router.tsx` comme la source React de l'application servie par `react.html` ; il distingue ce parcours des pages HTML et ressources historiques.

## 3. Frontend : routes React et écrans

Le routeur `frontend/src/app/router.tsx` définit les pages publiques, l'authentification et l'espace protégé `/app`.

| Route | Composant |
|---|---|
| `/` | HomePage |
| `/produit` | ProductPage |
| `/fonctionnement` | MethodPage |
| `/securite` | SecurityPage |
| `/tarifs` | PricingPage |
| `/contact` | ContactPage |
| `/mentions-legales`, `/confidentialite`, `/cookies`, `/cgu`, `/cgv` | LegalPage |
| `/login`, `/register` | LoginPage, RegisterPage |
| `/app/dashboard` | DashboardPage |
| `/app/reviews`, `/app/reviews/:id` | ReviewsPage, ReviewDetailPage |
| `/app/cases`, `/app/cases/:id` | CasesPage, CaseDetailPage |
| `/app/analysis` | AnalysisPage |
| `/app/notifications` | NotificationsPage |
| `/app/billing` | BillingPage |
| `/app/settings`, `/app/privacy`, `/app/admin` | SettingsPage, PrivacyPage, AdminPage |

Le groupe `/app` est enveloppé par `RequireAuth` et `AppShell`. La protection de route améliore l'expérience utilisateur ; les permissions réelles restent contrôlées côté API.

## 4. API : familles de routes repérées dans src/api_server.py

Les routes ci-dessous sont regroupées par domaine à partir des conditions de dispatch HTTP explicites du serveur. Pour les routes paramétrées, consulter la condition complète dans `src/api_server.py`.

| Domaine | Préfixes / exemples |
|---|---|
| Santé et exploitation | `/health`, `/healthz`, `/ready`, `/metrics` |
| Authentification | `/v1/auth/*`, récupération, inscription, connexion, MFA, sessions, changement de mot de passe |
| Organisation | `/v1/organization/*`, invitations, membres, rôles, calendrier SLA |
| Google | `/v1/integrations/google/*` |
| Avis | `/v1/reviews`, `/v1/reviews/{id}` |
| Dossiers | `/v1/cases/*`, workspace, cycle de vie et décisions |
| Preuves | `/v1/evidence/*`, documents client et téléchargement |
| File de revue et SLA | `/v1/review-queue/*`, `/v1/escalations/*` |
| Notifications | `/v1/notifications/*`, politiques et préférences |
| Facturation | `/v1/billing/*`, `/v1/paypal/*` |
| Confidentialité | `/v1/privacy/*` |

L'API est un dispatch centralisé dans `ReviewDefenseAPI.handle()`. Les services métier sont construits dans son initialiseur ; ils ne constituent pas chacun un serveur HTTP indépendant.

## 5. Frontières des couches

| Couche | Emplacement de référence | Responsabilité |
|---|---|---|
| Entrée HTTP | `wsgi.py`, `src/api_server.py` | Routage WSGI, authentification, validation, permissions et réponse |
| Services métier | `src/case_*.py`, `src/billing_service.py`, `src/notification_*.py` | Règles, transitions, orchestration |
| Intégrations | `src/google_*.py`, `src/paypal_client.py`, SMTP | Protocoles avec fournisseurs externes |
| Persistance | `src/postgres_*.py` | Transactions, contexte tenant, traduction SQL |
| Preuves | `src/evidence_*.py` | Stockage, OCR et extraction |
| Frontend | `frontend/src/**` | Présentation, navigation et appels API |
| Opérations | `scripts/**`, Compose, Dockerfile, workflows | Démarrage, migration, maintenance et déploiement |

## 6. Inventaire des fichiers

Les listes suivantes sont exhaustives pour les extensions et périmètres indiqués dans l'arbre Git observé. Elles servent d'index de navigation, pas de déclaration d'activité runtime.


### Runtime Python — src/ (76)

- `src/__init__.py`
- `src/alert_workspace.py`
- `src/analytics_workspace.py`
- `src/api_server.py`
- `src/app.py`
- `src/app_shell.py`
- `src/background_jobs.py`
- `src/billing.py`
- `src/billing_catalog.py`
- `src/billing_service.py`
- `src/business_calendar.py`
- `src/case_approval_service.py`
- `src/case_contradiction_service.py`
- `src/case_decision_service.py`
- `src/case_escalation_service.py`
- `src/case_evidence_matrix_service.py`
- `src/case_lifecycle_service.py`
- `src/case_operations_service.py`
- `src/case_review.py`
- `src/case_review_matrix.py`
- `src/case_review_service.py`
- `src/case_service.py`
- `src/case_sla_service.py`
- `src/case_submission_service.py`
- `src/case_workspace_service.py`
- `src/config.py`
- `src/contradiction_disposition.py`
- `src/contradiction_engine.py`
- `src/database.py`
- `src/decision_workspace.py`
- `src/deployment.py`
- `src/e2e_pipeline.py`
- `src/errors.py`
- `src/escalation_workflow.py`
- `src/evidence_extraction.py`
- `src/evidence_ocr.py`
- `src/evidence_vault.py`
- `src/google_business_profile.py`
- `src/google_integration.py`
- `src/google_pubsub_receiver.py`
- `src/google_sync_engine.py`
- `src/identity.py`
- `src/identity_repository.py`
- `src/mfa.py`
- `src/migration_runner.py`
- `src/notification_delivery.py`
- `src/notification_observability.py`
- `src/notification_outbox.py`
- `src/notification_policy.py`
- `src/notification_service.py`
- `src/notification_worker.py`
- `src/observability.py`
- `src/operations_ui.py`
- `src/ops_alerts.py`
- `src/outcome_workspace.py`
- `src/paypal_client.py`
- `src/policy_workspace.py`
- `src/postgres_api_repository.py`
- `src/postgres_integration.py`
- `src/postgres_notification_worker.py`
- `src/postgres_processing.py`
- `src/postgres_repository.py`
- `src/postgres_sync.py`
- `src/privacy_service.py`
- `src/processing_jobs.py`
- `src/production_config.py`
- `src/recovery_email.py`
- `src/resilience.py`
- `src/review_queue.py`
- `src/review_sla.py`
- `src/review_workspace.py`
- `src/security_hardening.py`
- `src/seo_content.py`
- `src/seo_renderer.py`
- `src/seo_site.py`
- `src/submission_workspace.py`

### Backend organisé par domaine — backend/ (75)

- `backend/analysis/analytics_workspace.py`
- `backend/analysis/case_contradiction_service.py`
- `backend/analysis/case_evidence_matrix_service.py`
- `backend/analysis/contradiction_disposition.py`
- `backend/analysis/contradiction_engine.py`
- `backend/analysis/evidence_extraction.py`
- `backend/analysis/evidence_ocr.py`
- `backend/analysis/evidence_vault.py`
- `backend/analysis/notification_policy.py`
- `backend/analysis/outcome_workspace.py`
- `backend/analysis/policy_workspace.py`
- `backend/api/__init__.py`
- `backend/api/api_server.py`
- `backend/api/app.py`
- `backend/api/app_shell.py`
- `backend/api/background_jobs.py`
- `backend/api/business_calendar.py`
- `backend/api/config.py`
- `backend/api/database.py`
- `backend/api/deployment.py`
- `backend/api/e2e_pipeline.py`
- `backend/api/errors.py`
- `backend/api/migration_runner.py`
- `backend/api/observability.py`
- `backend/api/operations_ui.py`
- `backend/api/postgres_api_repository.py`
- `backend/api/postgres_integration.py`
- `backend/api/postgres_processing.py`
- `backend/api/postgres_repository.py`
- `backend/api/postgres_sync.py`
- `backend/api/privacy_service.py`
- `backend/api/processing_jobs.py`
- `backend/api/production_config.py`
- `backend/api/resilience.py`
- `backend/api/seo_content.py`
- `backend/api/seo_renderer.py`
- `backend/api/seo_site.py`
- `backend/authentication/identity.py`
- `backend/authentication/identity_repository.py`
- `backend/authentication/mfa.py`
- `backend/authentication/recovery_email.py`
- `backend/authentication/security_hardening.py`
- `backend/billing/billing_catalog.py`
- `backend/billing/billing_service.py`
- `backend/billing/paypal_client.py`
- `backend/cases/case_approval_service.py`
- `backend/cases/case_decision_service.py`
- `backend/cases/case_escalation_service.py`
- `backend/cases/case_lifecycle_service.py`
- `backend/cases/case_operations_service.py`
- `backend/cases/case_service.py`
- `backend/cases/case_sla_service.py`
- `backend/cases/case_submission_service.py`
- `backend/cases/case_workspace_service.py`
- `backend/cases/decision_workspace.py`
- `backend/cases/escalation_workflow.py`
- `backend/cases/submission_workspace.py`
- `backend/notifications/alert_workspace.py`
- `backend/notifications/notification_delivery.py`
- `backend/notifications/notification_observability.py`
- `backend/notifications/notification_outbox.py`
- `backend/notifications/notification_service.py`
- `backend/notifications/notification_worker.py`
- `backend/notifications/ops_alerts.py`
- `backend/notifications/postgres_notification_worker.py`
- `backend/reviews/case_review.py`
- `backend/reviews/case_review_matrix.py`
- `backend/reviews/case_review_service.py`
- `backend/reviews/google_business_profile.py`
- `backend/reviews/google_integration.py`
- `backend/reviews/google_pubsub_receiver.py`
- `backend/reviews/google_sync_engine.py`
- `backend/reviews/review_queue.py`
- `backend/reviews/review_sla.py`
- `backend/reviews/review_workspace.py`

### Scripts opérationnels — scripts/ (30)

- `scripts/bootstrap_owner.py`
- `scripts/browser_e2e.py`
- `scripts/business_chain_certification.py`
- `scripts/demo_seed.py`
- `scripts/deploy_staging.py`
- `scripts/dr_validate.py`
- `scripts/github_staging_contract.py`
- `scripts/hourly_premium_maintenance.py`
- `scripts/migrate.py`
- `scripts/paypal/setup_sandbox.py`
- `scripts/postgres_backup.py`
- `scripts/postgres_certification.py`
- `scripts/postgres_restore.py`
- `scripts/postgres_smoke.py`
- `scripts/production_check.py`
- `scripts/provision_e2e_account.py`
- `scripts/public_browser_smoke.py`
- `scripts/release_candidate_gate.py`
- `scripts/release_check.py`
- `scripts/sandbox_certification.py`
- `scripts/sandbox_seed.py`
- `scripts/staging_certification.py`
- `scripts/staging_check.py`
- `scripts/staging_e2e.py`
- `scripts/uat_environment_readiness.py`
- `scripts/uat_seed.py`
- `scripts/uat_v640_certification.py`
- `scripts/uat_v640_execute.py`
- `scripts/v640_final_certification.py`
- `scripts/worker.py`

### Frontend React source — frontend/src/ (79)

- `frontend/src/app/router.tsx`
- `frontend/src/auth/AuthContext.tsx`
- `frontend/src/auth/RequireAuth.tsx`
- `frontend/src/auth/sessionToken.ts`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/BackLink.tsx`
- `frontend/src/components/layout/DetailMeta.tsx`
- `frontend/src/components/layout/FeedbackMessage.tsx`
- `frontend/src/components/layout/PageHeading.tsx`
- `frontend/src/components/layout/PublicFooter.tsx`
- `frontend/src/components/layout/PublicHeader.tsx`
- `frontend/src/components/layout/SectionHeading.tsx`
- `frontend/src/components/layout/SignalRow.tsx`
- `frontend/src/components/layout/StatusPill.tsx`
- `frontend/src/components/public/muse/MuseFooter.tsx`
- `frontend/src/components/public/muse/MuseHeader.tsx`
- `frontend/src/components/public/muse/MuseScene.tsx`
- `frontend/src/components/public/muse/MuseShell.tsx`
- `frontend/src/components/public/muse/PageBlocks.tsx`
- `frontend/src/components/public/muse/PublicActionLink.tsx`
- `frontend/src/components/public/muse/contact/ContactHero.tsx`
- `frontend/src/components/public/muse/contact/ContactLinks.tsx`
- `frontend/src/components/public/muse/contact/ContactNext.tsx`
- `frontend/src/components/public/muse/home/HomeBlocks.tsx`
- `frontend/src/components/public/muse/home/HomeChat.tsx`
- `frontend/src/components/public/muse/home/HomeData.ts`
- `frontend/src/components/public/muse/home/HomeFaq.tsx`
- `frontend/src/components/public/muse/home/HomeHero.tsx`
- `frontend/src/components/public/muse/home/HomeProducts.tsx`
- `frontend/src/components/public/muse/home/HomeResearch.tsx`
- `frontend/src/components/public/muse/home/HomeResearchDetail.tsx`
- `frontend/src/components/public/muse/home/HomeResponsibility.tsx`
- `frontend/src/components/public/muse/home/HomeSocial.tsx`
- `frontend/src/components/public/muse/home/HomeTry.tsx`
- `frontend/src/components/public/muse/home/HomeWorkspace.tsx`
- `frontend/src/components/public/muse/method/MethodHero.tsx`
- `frontend/src/components/public/muse/method/MethodLogic.tsx`
- `frontend/src/components/public/muse/method/MethodNext.tsx`
- `frontend/src/components/public/muse/method/MethodSteps.tsx`
- `frontend/src/components/public/muse/pricing/PricingCatalog.tsx`
- `frontend/src/components/public/muse/pricing/PricingHero.tsx`
- `frontend/src/components/public/muse/pricing/PricingNext.tsx`
- `frontend/src/components/public/muse/product/ProductHero.tsx`
- `frontend/src/components/public/muse/product/ProductMoments.tsx`
- `frontend/src/components/public/muse/product/ProductNext.tsx`
- `frontend/src/components/public/muse/product/ProductWorkspace.tsx`
- `frontend/src/components/public/muse/security/SecurityControls.tsx`
- `frontend/src/components/public/muse/security/SecurityFaq.tsx`
- `frontend/src/components/public/muse/security/SecurityHero.tsx`
- `frontend/src/components/public/muse/security/SecurityNext.tsx`
- `frontend/src/components/public/muse/security/SecurityResponsibility.tsx`
- `frontend/src/components/public/muse/useMuseMotion.ts`
- `frontend/src/components/ui/Button.tsx`
- `frontend/src/hooks/useApi.ts`
- `frontend/src/main.tsx`
- `frontend/src/pages/AdminPage.tsx`
- `frontend/src/pages/AnalysisPage.tsx`
- `frontend/src/pages/BillingPage.tsx`
- `frontend/src/pages/CaseDetailPage.tsx`
- `frontend/src/pages/CasesPage.tsx`
- `frontend/src/pages/ContactPage.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/HomePage.tsx`
- `frontend/src/pages/LegalPage.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/MethodPage.tsx`
- `frontend/src/pages/NotFoundPage.tsx`
- `frontend/src/pages/NotificationsPage.tsx`
- `frontend/src/pages/PricingPage.tsx`
- `frontend/src/pages/PrivacyPage.tsx`
- `frontend/src/pages/ProductPage.tsx`
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/pages/ReviewDetailPage.tsx`
- `frontend/src/pages/ReviewsPage.tsx`
- `frontend/src/pages/SecurityPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/services/api/client.ts`
- `frontend/src/types/api.ts`
- `frontend/src/vite-env.d.ts`

### Frontend historique et ressources — frontend/ (58)

- `frontend/about.html`
- `frontend/application/dashboard/workspace.css`
- `frontend/application/dashboard/workspace.html`
- `frontend/application/dashboard/workspace.js`
- `frontend/application/services/api/client.ts`
- `frontend/assets/app.css`
- `frontend/assets/app.js`
- `frontend/assets/billing.js`
- `frontend/assets/compliance-front.js`
- `frontend/assets/console-components.js`
- `frontend/assets/console-router.js`
- `frontend/assets/dossier-timeline.css`
- `frontend/assets/home.css`
- `frontend/assets/home.js`
- `frontend/assets/i18n.js`
- `frontend/assets/premium-console-v640.css`
- `frontend/assets/public.css`
- `frontend/assets/public.js`
- `frontend/assets/seo-articles.js`
- `frontend/assets/seo-renderer.js`
- `frontend/assets/seo.css`
- `frontend/assets/ui-components.js`
- `frontend/auth/AuthContext.tsx`
- `frontend/dist/assets/index-BR_ofpui.css`
- `frontend/dist/assets/index-WjhRtbEt.js`
- `frontend/dist/index.html`
- `frontend/fonctionnement.html`
- `frontend/index.html`
- `frontend/landing.html`
- `frontend/public/assets/js/public.js`
- `frontend/public/components/muse/pricing/PricingCatalog.tsx`
- `frontend/public/pages/about.html`
- `frontend/public/pages/fonctionnement.html`
- `frontend/public/pages/index.html`
- `frontend/public/pages/resources.html`
- `frontend/public/pages/resources/audit-e-reputation.html`
- `frontend/public/pages/resources/gestion-des-avis.html`
- `frontend/public/pages/services.html`
- `frontend/public/pages/tarif.html`
- `frontend/public/styles/global.css`
- `frontend/public/styles/muse-v3.css`
- `frontend/public/styles/public-secondary.css`
- `frontend/public/styles/style.css`
- `frontend/public/styles/styles.css`
- `frontend/public/styles/tokens.css`
- `frontend/react.html`
- `frontend/resources.html`
- `frontend/resources/audit-e-reputation.html`
- `frontend/resources/gestion-des-avis.html`
- `frontend/script.js`
- `frontend/services.html`
- `frontend/style.css`
- `frontend/styles.css`
- `frontend/tarif.html`
- `frontend/vite.config.ts`
- `frontend/workspace.css`
- `frontend/workspace.html`
- `frontend/workspace.js`

### Migrations de démarrage — migrations/ (35)

- `migrations/001_initial.sql`
- `migrations/002_v59_google_sync.sql`
- `migrations/003_v61_api_persistence.sql`
- `migrations/004_v62_identity.sql`
- `migrations/005_v65_contradiction_facts.sql`
- `migrations/006_v66_fact_suggestions.sql`
- `migrations/007_v67_review_queue.sql`
- `migrations/008_v68_sla_workload.sql`
- `migrations/009_v69_sla_controls.sql`
- `migrations/010_v610_business_calendar.sql`
- `migrations/011_v611_notification_outbox.sql`
- `migrations/012_v612_notification_delivery.sql`
- `migrations/013_v613_notification_worker.sql`
- `migrations/014_v614_notification_policies.sql`
- `migrations/015_v617_case_review.sql`
- `migrations/016_v618_contradiction_dispositions.sql`
- `migrations/017_v619_review_history_matrix.sql`
- `migrations/018_v620_production_foundation.sql`
- `migrations/019_v621_auth_hardening.sql`
- `migrations/020_v622_data_reliability.sql`
- `migrations/021_v624_auth_advanced.sql`
- `migrations/022_v625_identity_email.sql`
- `migrations/023_v640_session_restore.sql`
- `migrations/023_v70_paypal_billing.sql`
- `migrations/024_v641_rgpd_privacy_workflow.sql`
- `migrations/025_admin_only_mfa.sql`
- `migrations/026_v641_paypal_billing.sql`
- `migrations/027_v642_billing_identifier_integrity.sql`
- `migrations/028_v643_security_hardening.sql`
- `migrations/029_v643_processing_architecture.sql`
- `migrations/030_v644_billing_account_state.sql`
- `migrations/031_v641_client_monitoring_hub.sql`
- `migrations/032_v641_google_oauth_state_callback_rls.sql`
- `migrations/033_v645_client_hub_force_rls.sql`
- `migrations/034_v646_force_privacy_billing_rls.sql`

### Migrations parallèles — database/migrations/ (30)

- `database/migrations/001_initial.sql`
- `database/migrations/002_v59_google_sync.sql`
- `database/migrations/003_v61_api_persistence.sql`
- `database/migrations/004_v62_identity.sql`
- `database/migrations/005_v65_contradiction_facts.sql`
- `database/migrations/006_v66_fact_suggestions.sql`
- `database/migrations/007_v67_review_queue.sql`
- `database/migrations/008_v68_sla_workload.sql`
- `database/migrations/009_v69_sla_controls.sql`
- `database/migrations/010_v610_business_calendar.sql`
- `database/migrations/011_v611_notification_outbox.sql`
- `database/migrations/012_v612_notification_delivery.sql`
- `database/migrations/013_v613_notification_worker.sql`
- `database/migrations/014_v614_notification_policies.sql`
- `database/migrations/015_v617_case_review.sql`
- `database/migrations/016_v618_contradiction_dispositions.sql`
- `database/migrations/017_v619_review_history_matrix.sql`
- `database/migrations/018_v620_production_foundation.sql`
- `database/migrations/019_v621_auth_hardening.sql`
- `database/migrations/020_v622_data_reliability.sql`
- `database/migrations/021_v624_auth_advanced.sql`
- `database/migrations/022_v625_identity_email.sql`
- `database/migrations/023_v640_session_restore.sql`
- `database/migrations/024_v641_rgpd_privacy_workflow.sql`
- `database/migrations/025_admin_only_mfa.sql`
- `database/migrations/026_v641_paypal_billing.sql`
- `database/migrations/027_v642_billing_identifier_integrity.sql`
- `database/migrations/028_v643_security_hardening.sql`
- `database/migrations/029_v643_processing_architecture.sql`
- `database/migrations/030_v644_billing_account_state.sql`

### Entrées racine (10)

- `README.md`
- `bot.py`
- `docker-compose.production.yml`
- `docker-compose.staging.yml`
- `docker-compose.yml`
- `main.py`
- `prometheus.yml`
- `requirements.txt`
- `start.py`
- `wsgi.py`

## 7. Doublons structurels et précautions de migration

### Arborescences backend et src

Le dépôt contient à la fois des modules historiques dans `src/` et des modules regroupés par domaine dans `backend/`. Le point d'entrée WSGI sélectionne `src.api_server`. La présence de fichiers de noms proches dans `backend/` ne prouve pas qu'ils sont utilisés par les requêtes de production. Avant toute extraction, vérifier les imports, les factories, les workflows et les scripts consommateurs.

### Frontend React et frontend historique

Le dépôt contient `frontend/src/`, mais aussi des scripts, feuilles de style, pages et bundles historiques sous `frontend/`. Le routeur React ne remplace pas automatiquement les routes WSGI historiques. Toujours identifier le HTML servi et l'entrée JavaScript réellement chargée par la route étudiée.

### Deux répertoires de migrations

`scripts/migrate.py` calcule explicitement le chemin racine `migrations/` et lit uniquement les fichiers `migrations/*.sql`. Le dossier `database/migrations/` existe également dans le dépôt, mais il n'est pas sélectionné par ce script de démarrage. Ne pas supposer que les deux répertoires sont interchangeables ni copier une migration de l'un vers l'autre sans établir quel outil l'utilise.

Le répertoire `migrations/` contient notamment deux noms commençant par `023_`. Le script de démarrage enregistre le nom complet du fichier (stem) comme version, tandis que `src/migration_runner.py` extrait le préfixe numérique comme version. Ces deux runners n'ont donc pas exactement le même contrat d'identification. Il faut préserver ce constat lors de toute consolidation.

## 8. Méthode pour retracer une dépendance

Pour une fonction donnée, partir du consommateur et remonter la chaîne :

1. composant React ou route publique ;
2. méthode du client API et payload ;
3. condition HTTP dans `src/api_server.py` ;
4. contrôle identité, rôle et organisation ;
5. service métier appelé ;
6. adaptateur externe éventuel ;
7. repository et tables SQL ;
8. outbox ou file de travail, si le traitement est différé ;
9. réponse API et mise à jour de l'écran.

Une relation n'est considérée comme confirmée que si elle est visible dans un import, un appel, une instanciation ou une route explicite. Les noms de fichiers similaires, les répertoires de destination et les commentaires de roadmap ne suffisent pas.

## 9. Limites de cette cartographie

Cette carte couvre l'inventaire Git et les principaux chemins d'exécution. Elle ne prétend pas que chaque fonction de chacun des centaines de fichiers a été reliée à tous ses appelants. Les dépendances dynamiques (imports par chaîne, handlers configurés par environnement, plugins, scripts externes) demandent une analyse dédiée. Aucun code applicatif n'est modifié par ce document.
