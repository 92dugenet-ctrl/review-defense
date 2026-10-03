# Audit des permissions, rôles et de l'isolation inter-organisations — lot R

## Périmètre et méthode

Revue statique de `develop`, centrée sur le runtime WSGI/`src/api_server.py`, l'identité et les sessions, les repositories PostgreSQL, les migrations RLS et le routeur React. Les copies historiques sous `backend/` et les contrats historiques ne sont pas considérés comme une protection runtime sans raccordement démontré.

**Aucun test, build, typecheck, workflow, appel externe ou accès à une base réelle n'a été effectué.** Aucun compte, rôle, secret, document ou donnée métier n'a été modifié. Les constats sont statiques ; l'efficacité réelle de RLS dépend notamment du rôle PostgreSQL de connexion.

## Synthèse exécutive

L'authentification et l'isolation tenant ont des fondations réelles : bearer opaque, session persistée, rôle relu depuis l'appartenance, requêtes repository tenant-scoped et politiques RLS sur les tables principales.

Le principal déficit est la cohérence RBAC : plusieurs routes sensibles vérifient l'identité et le tenant, mais pas le rôle autorisé à lire ou modifier la ressource. Le frontend ne compense pas cet écart : `RequireAuth` vérifie la session, pas le rôle.

| Priorité | Constat | Conséquence possible |
|---|---|---|
| Élevée | POST /v1/reviews et POST /v1/evidence sans `_require_role` | VIEWER authentifié peut créer/modifier des données métier malgré le rôle lecture seule déclaré |
| Élevée | GET /v1/evidence/{id}/content et lectures de preuves sans garde de rôle | VIEWER peut lire le contenu des pièces, alors que la matrice historique ne lui donne pas accès à Evidence |
| Élevée | GET /v1/billing et /v1/billing/events sans garde de rôle | Les détails financiers sont accessibles à tout membre authentifié du tenant |
| Moyenne | GET /v1/organization/members sans garde | Emails et rôles des membres exposés à tous les rôles |
| Moyenne | GET /v1/client/documents et /download sans garde | Tous les rôles du tenant peuvent lister/télécharger les documents |
| Moyenne | GET /v1/review-queue sans garde | Données de pilotage accessibles aux rôles non opérateurs |
| Moyenne | GET /v1/integrations/google/locations sans garde | Métadonnées de connexions et établissements Google accessibles à tous les membres |
| Conditionnelle, élevée | FORCE RLS appliqué à certains groupes seulement | Si l'app se connecte comme propriétaire des tables, les politiques RLS non forcées peuvent être contournées |
| Moyenne | Fallback mémoire de facturation non filtré par tenant | En mode sans repository, les listes peuvent inclure des données d'autres organisations |

## 1. Authentification et rôle effectif

`ReviewDefenseAPI._auth()` :
- exige un bearer token, le transforme en hash et charge la session persistée ;
- relit l'état de révocation depuis PostgreSQL ;
- recharge le rôle effectif via `get_user_by_id(session.organization_id, session.user_id)` ;
- rejette une session si l'utilisateur n'est plus membre du tenant ;
- actualise l'activité de session.

Cela évite qu'un cache Gunicorn conserve un rôle élevé après une modification persistée. La recherche initiale de session sans tenant est une exception étroite : `get_session_by_token_hash()` utilise le hash opaque et la fonction SQL dédiée. Les lectures/écritures métier doivent rester tenant-scoped.

À préserver : ne jamais faire confiance au rôle transmis par le frontend, conserver la relecture du rôle par organisation, et ne jamais utiliser un `organization_id` client comme sélecteur de tenant.

## 2. Matrice des rôles et frontend

`src/app_shell.py` définit une matrice historique :
- OWNER/ADMIN : toutes les routes de ce shell ;
- ANALYST : toutes sauf settings ;
- CLIENT : dashboard, dossiers, avis, preuves, politiques détaillées, alertes et analytics ;
- VIEWER : dashboard, dossiers, avis et analytics, sans Evidence, Settings, Approvals, Submissions, Notifications ou Admin.

Ce module précise que cette matrice ne remplace pas les autorisations API. Elle décrit une intention, pas une protection effective.

Le routeur actuel `frontend/src/app/router.tsx` place toutes les pages sous `RequireAuth`. Cette garde attend une session valide mais n'applique pas de règle par rôle. Les pages admin, billing et notifications sont donc navigables par tout utilisateur connecté. L'écran Admin masque certaines options selon le rôle, mais ces contrôles visuels ne constituent pas une autorisation.

## 3. Routes métier sans garde RBAC

### Écriture d'avis et de preuves

`POST /v1/reviews` ne fait pas appel à `_require_role()`. Il effectue un upsert dans le tenant courant et journalise `REVIEW_INGESTED`.

`POST /v1/evidence` ne fait pas appel à `_require_role()`. Il vérifie le dossier dans le tenant, stocke le fichier, crée des faits proposés et persiste les métadonnées.

Le contrôle tenant est présent dans ces chemins, mais le contrôle de rôle manque. Un VIEWER peut donc appeler directement ces routes alors que son rôle est lecture seule dans la matrice historique.

**Remédiation :** définir les rôles autorisés pour ingestion d'avis et dépôt de preuve (OWNER/ADMIN/ANALYST/CLIENT selon la règle produit) et appliquer cette règle au backend.

### Lecture et contenu des preuves

`GET /v1/evidence`, `GET /v1/evidence/{id}` et `GET /v1/evidence/{id}/content` ne vérifient pas le rôle. Les recherches utilisent `user.organization_id` et le coffre est interrogé avec ce même tenant : le cloisonnement inter-organisations est présent dans le chemin observé.

La route `content` renvoie le fichier encodé en base64. L'absence de garde RBAC est donc particulièrement sensible : un VIEWER peut lire des pièces alors que la matrice historique ne lui donne pas accès à Evidence. Il faut distinguer permission de voir les métadonnées et permission de télécharger le contenu.

### File de traitement

`GET /v1/review-queue` n'impose pas de rôle ; il retourne priorité, affectation, SLA et éléments de dossier. À l'inverse, `GET /v1/review-queue/workload` exige OWNER/ADMIN/ANALYST. Cette asymétrie rend le périmètre de la file incohérent.

### Google

`GET /v1/integrations/google/locations` ne vérifie pas le rôle. Il lit les connexions du tenant et interroge Google pour retourner comptes et établissements. Le démarrage OAuth et la sélection d'emplacement vérifient OWNER/ADMIN/CLIENT ; le GET devrait suivre une règle explicite et cohérente.

## 4. Données d'organisation

### Facturation

`GET /v1/billing` et `GET /v1/billing/events` n'appliquent pas de garde de rôle. Avec PostgreSQL, les lectures sont bornées par `user.organization_id`, mais tout membre authentifié, y compris VIEWER, peut lire transactions, compte de facturation et événements. Il faut décider si les informations financières sont réservées OWNER/ADMIN ou si d'autres rôles y ont accès, puis appliquer la règle côté API.

Le fallback sans repository construit `rows` depuis `store.billing.values()` et `events` depuis `self.billing_events` sans filtre d'organisation explicite. Le démarrage production exige une base, mais ce chemin mémoire peut exposer des données inter-organisations dans les modes sans repository. Il doit être filtré par tenant ou supprimé.

### Membres

`GET /v1/organization/members` ne vérifie pas le rôle et retourne emails, identifiants et rôles de tous les membres du tenant. La création d'invitation et le changement de rôle exigent OWNER/ADMIN. La lecture devrait être alignée sur ce périmètre d'administration, sauf besoin produit documenté.

### Documents clients

`GET /v1/client/documents` et `GET /v1/client/documents/{id}/download` ne vérifient pas le rôle. Le téléchargement confirme que le document appartient au tenant puis lit le coffre avec ce tenant. Le POST de dépôt exige OWNER/ADMIN/CLIENT : lecture/téléchargement et écriture ont donc des règles asymétriques. Les documents peuvent contenir des pièces d'identité, contrats ou factures ; l'accès au contenu doit être défini explicitement.

## 5. Routes avec contrôles de rôle observés

Dans `src/api_server.py` :
- MFA enrollment/confirm/disable : OWNER/ADMIN ;
- invitations et changement de rôle : OWNER/ADMIN, avec restrictions spécifiques sur OWNER ;
- profil organisation et dépôt de documents : OWNER/ADMIN/CLIENT ;
- vérification de preuves/faits : OWNER/ADMIN/ANALYST ;
- file workload, affectations et escalades : généralement OWNER/ADMIN/ANALYST ;
- notification policy : lecture OWNER/ADMIN/ANALYST, écriture OWNER/ADMIN ;
- notifications et métriques : OWNER/ADMIN/ANALYST ;
- approbations, soumissions, décisions, gel et approbation : OWNER/ADMIN ;
- checklist : lecture tous rôles, modification OWNER/ADMIN/ANALYST.

Les rôles sont codés dans des listes locales au fil des handlers. Il n'existe pas de catalogue central par action/ressource ; cela rend les oublis de garde difficiles à détecter et les règles difficiles à maintenir.

## 6. Isolation tenant et RLS

### Isolation applicative

`PostgresRepository.transaction(organization_id)` refuse un tenant vide et installe `app.organization_id` avec `set_config(..., true)`, localement à la transaction. Les méthodes observées sont généralement tenant-scoped ; l'API utilise l'organisation issue de la session authentifiée.

### RLS activée

La migration initiale active RLS sur memberships, cases et case_events. La migration 003 active RLS et crée des politiques organisation pour les tables API, dont reviews, cases, decisions, snapshots, approvals, submissions, idempotency et evidence. D'autres migrations ajoutent les politiques sur invitations, événements de sécurité, récupération de compte et tables du hub client.

La migration 032 ajoute une politique spéciale pour le callback OAuth sans session tenant ; elle limite la lecture/suppression à l'état OAuth exact porté par `app.google_oauth_state`.

### Couverture FORCE RLS incomplète

Les migrations 033 et 034 appliquent FORCE RLS à certains groupes :
- 033 : organization_profiles, client_documents, google_connections, google_oauth_states ;
- 034 : privacy_requests, privacy_consents, billing_transactions.

Les tables cœur des migrations 001 et 003 ne figurent pas dans ces listes. Elles ont ENABLE RLS, mais les migrations examinées ne montrent pas FORCE RLS uniformément sur ces tables.

Le propriétaire d'une table peut normalement contourner RLS sauf si FORCE est activé. **Le risque dépend du rôle DB effectif** : si le compte applicatif est propriétaire des tables ou possède BYPASSRLS, les politiques seules ne constituent pas une barrière fiable. La configuration réelle n'a pas été inspectée.

**Remédiation :** confirmer les propriétaires et privilèges DB en environnement ; utiliser un rôle applicatif non propriétaire sans BYPASSRLS ; uniformiser FORCE RLS après inventaire des politiques et des exceptions OAuth.

## 7. Sessions et multi-organisation

Le repository met à jour l'appartenance et révoque les sessions de l'utilisateur dans l'organisation concernée lors d'un changement de rôle. L'API marque également les sessions mémoire de ce tenant comme révoquées. La requête suivante relit le statut de session et le rôle depuis PostgreSQL.

La résolution d'utilisateur est effectuée par couple organisation/utilisateur. Le changement de rôle interdit l'auto-modification et réserve l'attribution ou la rétrogradation d'un OWNER à un OWNER.

À vérifier lors d'une correction : les utilisateurs sont globaux alors que les rôles sont portés par memberships. Le cache `store.users` est indexé par user_id seul ; le chemin PostgreSQL relit bien l'appartenance par organisation, mais les chemins mémoire sans repository ne doivent pas traiter ce cache comme source de vérité multi-tenant.

## 8. Plan de remédiation

### Priorité 0
1. Ajouter une permission explicite à POST /v1/reviews et POST /v1/evidence.
2. Restreindre les routes de lecture/téléchargement des preuves par rôle.
3. Réserver GET /v1/review-queue aux rôles opérateurs.
4. Définir et appliquer les rôles autorisés pour GET /v1/billing et /v1/billing/events.
5. Définir les rôles autorisés pour les documents et téléchargements.

### Priorité 1
6. Créer un catalogue central de permissions par ressource/action.
7. Appliquer les contrôles aux routes membres et emplacements Google.
8. Aligner routeur, navigation, matrice des rôles et API ; le frontend reste une aide UX.
9. Filtrer par tenant tous les fallbacks mémoire, notamment la facturation.
10. Confirmer rôles DB, propriétaires et BYPASSRLS ; uniformiser FORCE RLS après vérification.
11. Vérifier les FK composites pour empêcher les références croisées entre organisations.

### Priorité 2
12. Documenter pour chaque rôle les données visibles et actions permises/interdites.
13. Auditer les changements de rôle, invitations, accès documents et exports.
14. Ajouter une revue systématique des nouvelles routes : identité, tenant, rôle, propriété de ressource et audit.

## 9. Fichiers examinés

`src/api_server.py`, `src/app_shell.py`, `src/identity_repository.py`, `src/security_hardening.py`, `src/postgres_api_repository.py`, `src/postgres_repository.py`, `frontend/src/app/router.tsx`, `frontend/src/auth/AuthContext.tsx`, `frontend/src/auth/RequireAuth.tsx`, `frontend/src/pages/AdminPage.tsx`, `frontend/src/pages/BillingPage.tsx`, `frontend/src/pages/NotificationsPage.tsx`, `migrations/001_initial.sql`, `migrations/003_v61_api_persistence.sql`, `migrations/004_v62_identity.sql`, `migrations/019_v621_auth_hardening.sql`, `migrations/021_v624_auth_advanced.sql`, `migrations/025_admin_only_mfa.sql`, `migrations/032_v641_google_oauth_state_callback_rls.sql`, `migrations/033_v645_client_hub_force_rls.sql`, `migrations/034_v646_force_privacy_billing_rls.sql`.

## Conclusion

Le socle d'authentification et de filtrage tenant est présent, notamment avec le rôle rechargé depuis l'appartenance et le contexte d'organisation par transaction. Le problème dominant est l'absence de vérification RBAC homogène sur plusieurs routes sensibles, en particulier l'écriture d'avis/preuves et la lecture de contenus, données financières et documents.

La couverture FORCE RLS est partielle dans les migrations examinées ; le risque dépend du rôle DB effectif et doit être confirmé sans supposer la configuration de production.

Ce lot est documentaire : aucun changement runtime, aucune migration et aucune opération sur des données réelles.
