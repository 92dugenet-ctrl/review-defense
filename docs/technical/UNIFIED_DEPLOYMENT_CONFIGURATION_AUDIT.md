# Lot L — Audit de cohérence de configuration et de déploiement

> Branche : `develop` — commit de référence : `63b0551c6a5a26ab11a1f29c71f3e43a9a252562`  
> Méthode : lecture statique des manifests, scripts, configuration runtime et workflows GitHub Actions.  
> Aucun secret consulté ou modifié. Aucun déploiement ni workflow lancé.

## 1. Niveaux de constat

- **Écart confirmé** : deux fichiers du dépôt décrivent des contrats incompatibles ou un consommateur attend une variable non transmise.
- **Risque conditionnel** : le problème dépend d'une option ou d'une configuration externe.
- **Point à confirmer** : le dépôt ne permet pas de connaître la valeur réellement configurée chez l'hébergeur.

L'audit ne lit pas les secrets GitHub, les variables privées de l'hébergeur, les volumes réels ni la configuration du proxy externe.

## 2. Synthèse

| Sujet | Constat | Conséquence possible |
|---|---|---|
| `.env.example` | Mode production avec URL HTTP locale et `TRUST_PROXY=false`. | Le pré-contrôle bloque le démarrage si le fichier est copié tel quel en production. |
| Variables Compose | SMTP, Google OAuth et PayPal webhook ne sont pas toutes transmises au conteneur. | Des intégrations restent non configurées même si les valeurs existent dans le fichier local de l'hôte. |
| Certification staging | Le script cherche migration, `SECURE_HEADERS` et `--workers 2` dans Compose. Ces paramètres sont définis ailleurs ou par défaut. | Les assertions contractuelles peuvent échouer à cause d'une recherche dans le mauvais fichier. |
| Worker | Aucun service worker n'est déclaré dans les Compose de production/staging ; le script traite un job par invocation. | Sans superviseur externe, les travaux peuvent ne pas être consommés en continu. |
| Environnement/proxy | `ProductionConfig` infère production depuis HTTPS ; `DeploymentConfig` ne le fait pas. | Certains contrôles proxy peuvent être désactivés si `REVIEW_DEFENSE_ENV` est absent. |
| Gunicorn | Les lanceurs utilisent des variables différentes ou des valeurs fixes. | Les réglages dépendent du point d'entrée effectivement utilisé. |
| Workflows | Déclencheurs, branches et effets diffèrent ; certains lancent tests, déploient ou poussent du code. | Un lancement ou push mal ciblé peut déclencher une opération non souhaitée. |

## 3. Variables d'environnement

### 3.1 Modèle de production incohérent

`.env.example` définit simultanément :

- `REVIEW_DEFENSE_ENV=production` ;
- `REVIEW_DEFENSE_PUBLIC_BASE_URL=http://localhost:8080` ;
- `TRUST_PROXY=false`.

`scripts/production_check.py` appelle `ProductionConfig.validate_startup()` puis `DeploymentConfig.validate()`. En production, ce dernier exige une URL HTTPS et `TRUST_PROXY=true`.

**Conclusion :** le fichier est un inventaire à adapter, pas un modèle de production prêt à copier. Il mélange des valeurs locales et un mode production explicite.

### 3.2 Variables consommées mais non transmises par les manifests Compose

Les fichiers Compose définissent explicitement l'environnement du service `app`. Un fichier `.env` peut servir à interpoler `${VARIABLE}`, mais ces valeurs ne sont pas automatiquement injectées dans le conteneur : il faut les déclarer dans `environment` ou `env_file`.

| Variables absentes de `environment` | Consommateur | Conséquence si aucune autre injection externe n'existe |
|---|---|---|
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_SENDER`, `SMTP_STARTTLS` | `ProductionConfig`, `recovery_email.py` | Le transport SMTP n'est pas configurable par ces manifests. |
| `REVIEW_DEFENSE_RECOVERY_EMAIL_ENABLED` | `ProductionConfig` | Les e-mails de récupération restent désactivés par défaut. |
| `REVIEW_DEFENSE_REQUIRE_EMAIL_VERIFICATION` | `ProductionConfig` | La vérification d'adresse reste désactivée par défaut. |
| `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` | `src/api_server.py` | OAuth Google est signalé non configuré. |
| `REVIEW_DEFENSE_GOOGLE_STATE_KEY` | `src/api_server.py` | La signature de l'état OAuth ne peut pas être configurée. |
| `REVIEW_DEFENSE_GOOGLE_TOKEN_KEY` | `src/api_server.py` | Le chiffrement des jetons Google ne peut pas être configuré. |
| `PAYPAL_WEBHOOK_ID` | `src/paypal_client.py` | La vérification de signature des webhooks échoue faute d'identifiant. |

Les manifests transmettent `PAYPAL_CLIENT_ID` et `PAYPAL_CLIENT_SECRET`, mais cela ne remplace pas `PAYPAL_WEBHOOK_ID`, utilisé séparément par `verify_webhook()`.

### 3.3 Variables absentes du modèle

Le modèle ne documente pas plusieurs variables utilisées par les manifests ou les scripts :

- `POSTGRES_PASSWORD` : requis par les Compose production/staging ;
- `REVIEW_DEFENSE_DOMAIN` et `TLS_ADMIN_EMAIL` : requis par Caddy en staging ;
- `PAYPAL_CLIENT_ID` : transmis aux conteneurs et lu par le client PayPal explicite ;
- `REVIEW_DEFENSE_WORKER_ORGANIZATION_ID`, `REVIEW_DEFENSE_WORKER_ID`, `REVIEW_DEFENSE_JOB_HANDLERS` : configuration du worker ;
- `WEB_CONCURRENCY`, `GUNICORN_WORKERS`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT` : réglages des lanceurs.

Ces variables sont spécifiques à des rôles différents : il faut documenter leur consommateur et le service qui doit les recevoir, plutôt que les injecter toutes partout.

## 4. Environnement et proxy

`src/production_config.py` déduit l'environnement : si `REVIEW_DEFENSE_ENV` est absent, une URL publique HTTPS implique `production`.

`src/deployment.py` lit seulement `REVIEW_DEFENSE_ENV` et utilise `development` par défaut. Le contrôle pré-démarrage appelle les deux validateurs.

**Écart confirmé :** avec une URL HTTPS mais sans `REVIEW_DEFENSE_ENV`, la configuration applicative se considère en production alors que le contrat de proxy se considère en développement. Le contrôle strict `TRUST_PROXY=true` de `DeploymentConfig` n'est alors pas appliqué.

Les manifests officiels staging et production définissent explicitement `REVIEW_DEFENSE_ENV=production`, ce qui évite ce cas dans ces deux stacks. Le risque concerne les autres déploiements reposant sur l'inférence.

Autre détail : `HOST` est validé par la configuration, mais `scripts/start_production.sh` passe toujours `--bind 0.0.0.0:...` à Gunicorn. Modifier `HOST` ne change donc pas l'adresse d'écoute de ce lanceur.

## 5. Démarrage et paramètres Gunicorn

| Entrée | Paramètres observés |
|---|---|
| `Dockerfile` | Lance `scripts/start_production.sh`. |
| `scripts/start_production.sh` | Contrôle → migrations → Gunicorn ; `WEB_CONCURRENCY` ou 2 workers ; timeout 60 s. |
| `main.py` | `wsgi:app), variables `GUNICORN_WORKERS`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT`. |
| `start.py` | `wsgi:app), 2 workers, 4 threads et timeout 60 s codés en dur. |
| `bot.py` | `wsgi:app), 2 workers, 4 threads, timeout 60 s ; port par défaut 25875. |

Tous convergent vers `wsgi:app`, mais leurs réglages ne sont pas uniformes. Le Dockerfile n'utilise ni `main.py`, ni `start.py`, ni `bot.py`.

**Décision :** conserver les adaptateurs tant que leurs plateformes sont identifiées ; documenter la commande réellement configurée chez chaque hébergeur avant de modifier un lanceur.

## 6. Worker asynchrone

Les Compose production/staging déclarent PostgreSQL et l'application web ; staging ajoute Caddy. Aucun service `worker` n'est déclaré.

`scripts/worker.py` :
- exige `DATABASE_URL` et `REVIEW_DEFENSE_WORKER_ORGANIZATION_ID` ;
- réserve au maximum un job avec `queue.claim(...)` ;
- traite ce job puis le marque terminé ou en échec ;
- termine le processus après cette invocation ;
- lit les handlers depuis `REVIEW_DEFENSE_JOB_HANDLERS`.

Le script importe `PostgresNotificationWorker`, mais `run_processing_once()` ne l'instancie pas et ne consomme pas explicitement l'outbox.

**Conséquence :** si aucun ordonnanceur ou superviseur externe n'existe chez l'hébergeur, les jobs ne seront pas consommés en continu. Le fait que le script soit dans l'image ne le lance pas automatiquement.

## 7. Certification staging : assertions non alignées

`scripts/staging_certification.py` inspecte le texte de `docker-compose.staging.yml` et attend notamment :

| Assertion recherchée dans Compose | Emplacement réel |
|---|---|
| `"python scripts/migrate.py"` | `scripts/start_production.sh`, appelé par le `CMD` du Dockerfile. |
| `'SECURE_HEADERS: "true"'` | Non déclaré dans Compose ; `ProductionConfig` a `secure_headers=True` par défaut. |
| `"--workers 2"` | `scripts/start_production.sh` utilise `WEB_CONCURRENCY`, défaut 2. |

Ces trois assertions ne correspondent pas à l'emplacement réel des paramètres. Le workflow staging appelle ce script ; son rapport contractuel peut donc échouer à cause de vérifications textuelles trop strictes, même si le démarrage réel définit ces valeurs indirectement.

Deux options sont à arbitrer : déclarer explicitement ces paramètres dans le manifeste, ou faire vérifier par le script les fichiers qui possèdent réellement chaque contrat. Aucune assertion n'est modifiée dans ce lot.

## 8. Workflows GitHub Actions

| Workflow | Déclencheur | Effet / précaution |
|---|---|---|
| `ci.yml` | Push `develop`, PR vers `main`/`develop`, manuel | Migrations et tests. |
| `frontend.yml` | Push `main`/`develop` si frontend modifié, PR frontend | Typecheck/build ; peut synchroniser dist sur push `main`. |
| `react-build.yml` | Push `main`/`develop` ou PR si frontend modifié, manuel | Typecheck et build React. |
| `foundation.yml`, `processing.yml`, `security.yml` | Manuels | Compilation et tests. |
| `billing.yml` | Push `main`, manuel | Build image, migrations, tests d'intégration et régression. |
| `review-defense-staging.yml` | Push `main`/branche feature nommée, PR vers `main`, manuel | Tests, certifications et étapes staging/E2E conditionnelles ; pas de push automatique sur `develop`. |
| `preproduction.yml` | Manuel | SSH et déploiement distant. |
| `hourly-premium-maintenance.yml` | Cron horaire, manuel | Checkout explicite de `main`, maintenance, test frontend et possibilité de push sur `main`. |
| `paypal-sandbox-provision.yml` | Manuel | Provisionne PayPal Sandbox et publie un artefact de configuration. |

Points de vigilance :

- Un push sur `develop` correspond au déclencheur de `ci.yml`. GitHub Actions reconnaît le marqueur `[skip ci]` dans le message d'un commit pour ignorer les workflows `push` et `pull_request`.
- `hourly-premium-maintenance.yml` cible `main`, contient une étape de test et peut pousser un commit : ne pas le déclencher.
- `review-defense-staging.yml` n'a pas de push sur `develop`, mais son lancement manuel exécute des jobs avec tests et certifications.
- `preproduction.yml` est un déploiement distant, pas un contrôle documentaire. Il récupère `main` sur le serveur puis tente de checkout le SHA du workflow ; un lancement manuel depuis un commit non présent dans l'historique récupéré peut échouer.
- `frontend.yml` et `react-build.yml` sont filtrés par chemins frontend ; les modifications documentaires de ce lot ne touchent pas ces chemins.

Aucun workflow n'a été lancé dans le cadre du lot L.

## 9. Décisions à prendre avant correction

| Domaine | Décision à clarifier |
|---|---|
| Modèle d'environnement | Séparer modèles local, staging et production ou expliciter que le modèle unique n'est pas prêt à l'emploi. |
| SMTP | Activer ou non récupération et vérification d'adresse ; définir les secrets à transmettre. |
| Google | Confirmer les environnements où OAuth est actif et la façon d'injecter les clés. |
| PayPal | Associer le `PAYPAL_WEBHOOK_ID` correct à chaque environnement. |
| Worker | Définir superviseur, fréquence, tenant, handlers et processus de livraison des notifications. |
| Proxy | Fixer explicitement environnement et confiance proxy sur tous les déploiements HTTPS. |
| Gunicorn | Identifier le lanceur de chaque plateforme et uniformiser les variables supportées. |
| Certification | Vérifier les manifests ou les fichiers réellement propriétaires des paramètres. |
| Préproduction | Limiter les lancements à `main` ou gérer explicitement les autres branches. |

## 10. Ordre de correction proposé

1. Clarifier les contrats local, staging et production.
2. Relier chaque variable sensible à son consommateur et au service Docker qui doit la recevoir.
3. Définir le mode d'exploitation des workers et leurs handlers.
4. Aligner les contrôles de certification sur les bons fichiers.
5. Uniformiser l'inférence d'environnement entre les deux configurations.
6. Documenter les lanceurs et paramètres Gunicorn de chaque plateforme.
7. Encadrer les workflows de déploiement et leur branche source.

Aucune correction de configuration ou de comportement n'est appliquée dans ce lot : certaines décisions nécessitent des informations de l'hébergeur absentes du dépôt.

## 11. Limites et conclusion

L'audit confirme des écarts dans les modèles, l'injection de variables et les assertions statiques. Il ne permet pas de savoir si l'hébergeur injecte des variables supplémentaires, supervise déjà le worker ou désactive certains workflows.

Il faut distinguer quatre niveaux : variables présentes dans un fichier local, variables interpolées par Compose, variables réellement transmises au conteneur, valeurs lues par le code au démarrage ou à la requête. Ces niveaux ne sont pas équivalents.

**Aucun test, build, typecheck, smoke check, certification, déploiement ou workflow n'a été exécuté.** L'audit repose uniquement sur la lecture des fichiers et la comparaison statique des contrats.
