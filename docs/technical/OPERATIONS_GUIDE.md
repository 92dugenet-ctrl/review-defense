# Guide d'exploitation et de configuration

Ce document complète le guide de lecture du code. Il explique les points d'entrée opérationnels, les responsabilités des scripts et les relations entre les fichiers.

## 1. Démarrage en production

Le parcours est : Docker/Compose → `scripts/start_production.sh` → `scripts/production_check.py` → `scripts/migrate.py` → Gunicorn (`wsgi:app`) → `src.api_server`.

- **Dockerfile** construit le frontend React/Vite dans une image Node, puis copie les ressources compilées dans l'image Python finale. Node n'est pas nécessaire au runtime.
- **start_production.sh** fournit des valeurs minimales, arrête le démarrage si le contrôle de configuration échoue, applique les migrations, puis remplace le shell par Gunicorn.
- **production_check.py** valide les paramètres applicatifs, l'URL publique, la relation au reverse proxy et DATABASE_URL. Il ne démarre pas le serveur.
- **migrate.py** applique les migrations SQL manquantes avant que l'API ne reçoive du trafic.
- **wsgi.py** expose l'application WSGI utilisée par Gunicorn.

Le préfixe `exec` devant Gunicorn lui permet de recevoir directement les signaux du processus conteneur. WEB_CONCURRENCY détermine le nombre de workers HTTP.

## 2. Configuration : responsabilités

| Fichier | Responsabilité |
|---|---|
| `.env.example` | Inventaire commenté des variables ; modèle, pas fichier de secrets |
| `src/config.py` | Paramètres historiques typés chargés par get_settings() |
| `src/production_config.py` | Paramètres de production et validation des prérequis |
| `src/deployment.py` | URL publique, confiance proxy et en-têtes HTTP |
| `docker-compose.staging.yml` | Stack de préproduction : PostgreSQL, application, proxy et volumes |
| `docker-compose.production.yml` | Stack de production : PostgreSQL et application, TLS fourni par un proxy externe |
| `Caddyfile` | Terminaison HTTPS, certificats automatiques, compression et reverse proxy |

Les valeurs sont injectées dans l'environnement du processus. Les secrets ne doivent pas être inscrits dans `.env.example`, les fichiers suivis par Git, le frontend ou les rapports. Ils doivent provenir du gestionnaire de secrets du déploiement.

Variables à comprendre en premier :
- `DATABASE_URL` : connexion PostgreSQL utilisée par l'API, les migrations et certains workers.
- `REVIEW_DEFENSE_ENV` : mode d'exécution et sélection des contrôles stricts.
- `REVIEW_DEFENSE_PUBLIC_BASE_URL` : URL canonique publique.
- `TRUST_PROXY` : confiance accordée aux en-têtes du proxy TLS.
- `REVIEW_DEFENSE_MFA_ENCRYPTION_KEY` : clé serveur de protection des secrets MFA.
- `REVIEW_DEFENSE_EVIDENCE_ROOT` : emplacement des preuves, à monter sur un volume persistant protégé.
- `SMTP_*` : transport des courriels transactionnels.
- `PAYPAL_*` et `GOOGLE_*` : identifiants et secrets des intégrations.

## 3. Migrations PostgreSQL

Les fichiers SQL de `migrations/` sont lus par `scripts/migrate.py`, triés par nom de fichier et enregistrés dans `schema_migrations`.

Le script crée le registre s'il manque, prend un verrou advisory PostgreSQL pour sérialiser les lanceurs concurrents, ignore les noms déjà enregistrés, applique les autres fichiers et enregistre leur version. Le nom du fichier sans extension est l'identifiant de migration. Une migration déjà enregistrée n'est pas rejouée automatiquement.

## 4. Serveur HTTP et workers

Le serveur HTTP et les workers sont deux processus distincts.

- **Gunicorn / WSGI** reçoit les requêtes web et les transmet à l'application API.
- **scripts/worker.py** démarre le consommateur de travaux persistés dans PostgreSQL. Il exige DATABASE_URL et REVIEW_DEFENSE_WORKER_ORGANIZATION_ID ; le périmètre tenant est explicite. REVIEW_DEFENSE_WORKER_ID identifie le processus et REVIEW_DEFENSE_JOB_HANDLERS associe les handlers importables aux types de travaux.
- **PostgresProcessingQueue** réserve les travaux et gère leur cycle de traitement. Le script `scripts/worker.py` ne traite qu'un seul job par invocation.
- **PostgresNotificationWorker** est un worker distinct de l'outbox ; son import dans `scripts/worker.py` ne signifie pas qu'il y est lancé. Son processus de supervision doit être identifié séparément.

Le worker n'est pas un second serveur HTTP. Il doit être déployé et supervisé comme un processus de fond distinct, avec les variables et permissions adaptées à son organisation.

## 5. Scripts d'exploitation

| Script | Usage et précaution |
|---|---|
| `production_check.py` | Contrôle bloquant des paramètres avant démarrage |
| `migrate.py` | Applique les migrations SQL absentes |
| `worker.py` | Lance un cycle de traitement asynchrone tenant-scoped |
| `bootstrap_owner.py` | Crée le premier OWNER ; opération ponctuelle d'initialisation |
| `postgres_backup.py` | Produit une sauvegarde PostgreSQL au format custom |
| `postgres_restore.py` | Restaure une sauvegarde ; opération destructive avec confirmation explicite |
| `staging_check.py` | Interroge /health et /ready sur la préproduction |
| `release_check.py` | Vérifie statiquement la présence et la cohérence d'artefacts |
| `deploy_staging.py` | Vérifie le contrat de déploiement ; ne se connecte pas au serveur distant |
| `paypal/setup_sandbox.py` | Crée le produit et les plans PayPal Sandbox |
| `hourly_premium_maintenance.py` | Modifie certains garde-fous du site public, écrit un rapport et peut créer un commit Git |

Les scripts de sauvegarde et de restauration ne remplacent pas une politique de sauvegarde : il faut prévoir destination, rétention, protection des fichiers et procédure de restauration. Toute restauration doit viser explicitement la base prévue.

## 6. Workflows GitHub Actions

Les fichiers `.github/workflows/*.yml` décrivent des automatisations GitHub Actions. Ils ne sont pas des composants du serveur applicatif.

- **hourly-premium-maintenance.yml** : cron à la minute 17 de chaque heure et déclenchement manuel. Le workflow checkout explicitement `main`, exécute la maintenance, contient aussi une étape de tests frontend et peut pousser un commit sur `main`. Le cron ne cible donc pas `develop`.
- **processing.yml** : déclenchement manuel ; installe les dépendances, compile des sources Python et lance une sélection de tests.
- **review-defense-staging.yml** : workflow de staging associé aux push sur certaines branches et aux pull requests vers `main`, avec déclenchement manuel possible. Il contient compilation, tests et étapes de certification.
- **preproduction.yml** : déclenchement manuel ; déploie sur l'environnement preproduction avec les secrets configurés dans GitHub.
- **paypal-sandbox-provision.yml** : déclenchement manuel ; provisionne les ressources PayPal Sandbox et publie un artefact de configuration à durée de rétention limitée.

D'autres workflows couvrent contrats frontend, facturation, sécurité, seeds de démonstration et certifications. Lire leur section `on:` avant toute action : le déclencheur, la branche checkoutée et les permissions déterminent leurs effets.

**Consigne de travail :** les workflows qui contiennent des commandes de tests ne doivent pas être déclenchés dans le cadre de nos opérations. Ce guide ne les exécute pas et leur présence dans GitHub ne signifie pas qu'ils ont été lancés pendant la documentation.

## 7. Volumes et réseau

- PostgreSQL conserve ses données dans un volume Docker nommé.
- Les preuves sont conservées dans un volume séparé, monté au chemin configuré par `REVIEW_DEFENSE_EVIDENCE_ROOT`.
- En staging, Caddy termine TLS et relaie le trafic vers le service `app:8080` sur le réseau Docker privé.
- En production, TLS peut être terminé par un proxy ou load balancer externe.
- `expose` rend un port accessible aux services du réseau Docker ; `ports` publie un mapping sur l'hôte.

## 8. Parcours de lecture recommandé

1. `Dockerfile` : construction de l'image et séparation build/runtime.
2. `docker-compose.staging.yml` ou `docker-compose.production.yml` : services, variables, volumes et réseau.
3. `scripts/start_production.sh` : séquence de démarrage.
4. `scripts/production_check.py` et `src/production_config.py` : conditions de démarrage.
5. `scripts/migrate.py` et `migrations/` : évolution du schéma.
6. `wsgi.py` et `src/api_server.py` : arrivée des requêtes HTTP.
7. `scripts/worker.py` et les modules `src/postgres_*` : traitement hors requête.

Ce parcours relie les fichiers de déploiement au code exécuté sans confondre scripts d'administration, workflows GitHub et services métier.

## 9. Audit de cohérence des déploiements — lot L

Consulter [UNIFIED_DEPLOYMENT_CONFIGURATION_AUDIT.md](./UNIFIED_DEPLOYMENT_CONFIGURATION_AUDIT.md) pour l'analyse des variables, manifests, proxy, lanceurs et workflows.

Points à retenir :

- `.env.example` est un inventaire, pas un fichier de production prêt à l'emploi : ses valeurs HTTP locales sont incompatibles avec `REVIEW_DEFENSE_ENV=production`.
- Docker Compose n'injecte que les variables déclarées dans `environment` ou `env_file`. Une variable disponible pour l'interpolation n'est pas automatiquement présente dans le processus applicatif.
- Les manifests production/staging ne transmettent pas toutes les variables SMTP, Google et PayPal consommées par l'application.
- Aucun service worker n'est déclaré dans les Compose ; `scripts/worker.py` traite un job par invocation et doit être supervisé séparément.
- Le script de certification staging vérifie certaines chaînes dans Compose alors que les commandes et valeurs sont définies dans le Dockerfile, le script de démarrage ou les valeurs par défaut applicatives.
- Les workflows ont des déclencheurs et effets distincts ; certains lancent des tests ou déploient sur des environnements distants.

Aucune configuration ni aucun comportement applicatif n'a été modifié dans le lot L.

## 10. Configuration unifiée — lot M

Les stacks Compose transmettent explicitement les variables facultatives SMTP,
OAuth Google et PayPal webhook au processus `app`. `PAYPAL_ENV` sélectionne
l'API PayPal : `production` pour la stack de production et `sandbox` pour
staging. Le vérificateur de webhook historique utilise ce même environnement.
L'envoi de courriels reste désactivé par défaut tant que SMTP n'est pas configuré.

Le lanceur Docker `scripts/start_production.sh` accepte les réglages
`GUNICORN_WORKERS`, `GUNICORN_THREADS` et `GUNICORN_TIMEOUT`.
`WEB_CONCURRENCY` reste un alias de compatibilité pour le nombre de workers.

`DeploymentConfig` applique la même inférence d'environnement que
`ProductionConfig` : en l'absence de `REVIEW_DEFENSE_ENV`, une URL publique
HTTPS implique la production.

Le contrat de certification staging vérifie les fichiers propriétaires
des paramètres : Dockerfile et script de démarrage pour l'ordre des migrations,
Compose et configuration applicative pour les en-têtes, script de démarrage
pour les paramètres Gunicorn.

Aucun service worker n'est ajouté aux stacks : `scripts/worker.py` traite
un seul job par invocation, et les handlers ainsi que le superviseur permanent
ne sont pas encore spécifiés. Les variables du worker figurent dans le modèle
d'environnement à titre de configuration d'un processus séparé.

## 11. Cycle de vie des données — lot N

Consulter [DATA_LIFECYCLE_AUDIT.md](./DATA_LIFECYCLE_AUDIT.md) pour le détail des migrations, sauvegardes, preuves, cloisonnement tenant et règles de conservation.

Repères opérationnels :

- Le démarrage de production applique `migrations/*.sql` via `scripts/migrate.py`. Le nom complet du fichier est l'identifiant de migration ; les empreintes SHA-256 et le nom sont conservés dans `schema_migrations`.
- `database/migrations/` est une arborescence historique incomplète et ne doit pas être synchronisée automatiquement.
- Les scripts `postgres_backup.py` et `postgres_restore.py` ne couvrent que PostgreSQL. Le volume `/data/evidence` exige une sauvegarde séparée et coordonnée.
- Les sauvegardes locales sont créées en permissions `0600`. Les mots de passe PostgreSQL sont transmis via `PGPASSWORD`, pas dans les arguments des processus.
- Aucune rétention ou purge automatique globale n'est déclarée par ces scripts. Les délais et règles d'effacement doivent être décidés et documentés avant exploitation.
- Les restaurations restent destructives et exigent une cible explicite ainsi que `--confirm`.


## 12. Suppressions et intégrité référentielle — lot O

Consulter [DELETION_INTEGRITY_AUDIT.md](./DELETION_INTEGRITY_AUDIT.md) avant toute suppression de compte, d'organisation, de dossier, de preuve ou de document.

Précautions :

- Le statut `COMPLETED` d'une demande `ERASURE` ne déclenche pas à lui seul l'effacement des données ou des fichiers.
- Plusieurs références utilisateur utilisent `RESTRICT` ou le comportement SQL par défaut `NO ACTION` ; une suppression physique d'utilisateur peut être bloquée par les demandes RGPD, événements de dossier, invitations ou documents.
- Les métadonnées SQL et les octets du coffre de preuves sont séparés. Une cascade SQL ne supprime pas les fichiers du volume.
- Certaines références dossier/preuve sont des identifiants sans clé étrangère. Leur intégrité dépend donc des services applicatifs.
- Ne pas ajouter de cascade ou modifier une contrainte publiée sans inventorier les données et contraintes déjà présentes dans les environnements.
- Une suppression coordonnée doit être durable, idempotente et reprenable, car PostgreSQL et le stockage de fichiers ne partagent pas une transaction atomique.


## 13. Traitements asynchrones et effets de bord — lot P

Consulter [ASYNC_PROCESSING_AUDIT.md](./ASYNC_PROCESSING_AUDIT.md) avant toute modification des files, workers, notifications, synchronisations Google ou webhooks PayPal.

Points de vigilance :
- Les leases PostgreSQL expirés remettent les jobs en attente sans appliquer `max_attempts`.
- Un handler peut réussir un effet externe puis tomber avant que le job soit marqué `completed`.
- Le worker PostgreSQL notification conserve une transaction et les verrous SQL pendant l'appel réseau.
- La route HTTP de worker notification utilise le worker applicatif mémoire, pas `PostgresNotificationWorker`.
- La déduplication SQL outbox reste unique après `SENT` ou `CANCELLED`, alors que le service ne vérifie en mémoire que les doublons `PENDING`.
- Le webhook PayPal persiste l'identifiant d'événement avant les écritures secondaires du compte et du journal ; un retry peut ne pas réparer ces écritures.
- `scripts/worker.py` traite un job par invocation et ne lance pas le worker PostgreSQL de notifications.

Les effets externes doivent être idempotents et rapprochés ; les réservations doivent être durables et courtes ; les reprises doivent rester bornées après expiration d'un lease. Aucun changement runtime n'est inclus dans ce lot.


## 14. Cohérence métier des dossiers — lot Q

Consulter [CASE_BUSINESS_CONSISTENCY_AUDIT.md](./CASE_BUSINESS_CONSISTENCY_AUDIT.md) avant toute modification des dossiers, décisions, snapshots, approbations, soumissions ou droits de facturation.

Points de vigilance :
- L'hydratation recharge le dossier, l'avis, les preuves et les faits, mais pas la décision ni le snapshot depuis PostgreSQL.
- Le contrôle d'approbation compare le snapshot à son propre payload, pas au dossier courant.
- Le snapshot ne comprend pas les preuves, faits vérifiés, contradictions/dispositions ni checklist.
- La création d'une décision met le dossier à ANALYZED alors que la décision est DRAFT.
- La route /submit crée seulement une soumission locale DRAFT avec external_call=false.
- Les écritures décision, snapshot, approbation et statut sont des transactions repository distinctes.
- Les statuts PayPal de billing.py ne sont pas tous classés comme actifs ou terminaux dans billing_service.py.

Priorités : intégrité/invalidation des snapshots, hydratation durable du contexte décisionnel, transitions d'état centralisées, puis harmonisation des statuts de facturation. Aucun changement runtime n'est inclus dans ce lot.
