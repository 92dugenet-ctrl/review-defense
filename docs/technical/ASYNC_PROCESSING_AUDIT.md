# Audit des traitements asynchrones et des effets de bord — lot P

## Périmètre

Revue statique de `develop` : files de jobs, workers, outbox, notifications, synchronisation Google, Pub/Sub, intégration PayPal, migrations et lanceurs.

**Aucun test, build, typecheck, workflow GitHub Actions, appel externe ni accès à une base réelle n'a été effectué.** Aucun état métier ou aucune donnée n'ont été modifiés. Les constats portent sur le code versionné, pas sur l'état d'un environnement déployé.

## Synthèse

Les mécanismes de base existent (files persistantes, clés d'idempotence, leases, reprises, outbox, journalisation), mais les garanties ne sont pas homogènes.

| Priorité | Constat | Conséquence possible |
|---|---|---|
| Critique | Webhook PayPal marqué comme vu avant la fin des écritures secondaires | Un retry peut être ignoré alors que le compte ou le journal n'a pas été mis à jour |
| Élevée | Worker PostgreSQL notification garde la transaction SQL pendant l'appel réseau | Verrous longs ; envoi répété après acceptation fournisseur puis rollback/crash |
| Élevée | Route HTTP utilise le worker notification mémoire, sans réservation SQL | Deux processus API peuvent envoyer la même notification |
| Élevée | Lease expiré d'un job remis en pending sans appliquer max_attempts | Reprises non bornées après crashes |
| Élevée | Handler et marquage completed sont deux opérations séparées | Effet externe rejoué si le processus tombe après l'effet |
| Moyenne | Clé de déduplication outbox reste unique après SENT/CANCELLED, service ne déduplique en mémoire que PENDING | Nouvelle notification locale fantôme si l'INSERT SQL est ignoré |
| Moyenne | scripts/worker.py ne traite qu'un job par invocation et ne lance pas le worker PostgreSQL de notifications | Besoin d'un superviseur et d'un raccordement explicites |

## 1. Files de jobs

### Abstractions coexistantes

- `src/background_jobs.py` : file SQLite historique, priorités, idempotence, leases, reprises et dead letters.
- `src/processing_jobs.py` : contrat de traitement et implémentation SQLite avec événements et empreinte du payload.
- `src/postgres_processing.py` : file PostgreSQL utilisée par `scripts/worker.py`.
- `src/postgres_sync.py` : autre file PostgreSQL, `background_jobs`, utilisée par le flux Pub/Sub/Google.

Ces implémentations ne partagent pas automatiquement les mêmes états, handlers ni garanties. Les modules parallèles `backend/` et les migrations historiques ne sont pas assimilés au runtime sans preuve de raccordement.

### Réservation et baux

`PostgresProcessingQueue.claim()` utilise `FOR UPDATE SKIP LOCKED`, incrémente `attempt`, affecte un worker et pose `leased_until`. La réservation et l'événement `claimed` sont enregistrés dans la transaction. `complete()` et `fail()` vérifient l'identité du worker propriétaire.

**Défaut :** `recover_expired_leases()` et la récupération incluse dans `claim()` replacent tout job expiré en `pending`, sans comparer `attempt` à `max_attempts`. Le chemin `fail()` borne les erreurs explicitement remontées, mais pas les crashes répétés après réservation. `src/processing_jobs.py` présente le même comportement dans `_recover()`.

Le lanceur réserve un bail de 60 secondes et ne renouvelle pas le bail pendant le handler. Un handler long peut donc être repris pendant que le premier processus travaille encore. Le contrôle de propriété protège la finalisation, pas l'effet externe déjà commencé.

### Fenêtre d'effet externe

Dans `scripts/worker.py`, le handler est exécuté avant `queue.complete()`. L'effet externe et la transition SQL ne sont pas atomiques. Si le fournisseur accepte l'action puis que le processus tombe avant la finalisation, le job peut être rejoué. La clé d'idempotence de l'enqueue empêche certains doublons de jobs, mais ne rend pas l'action du handler idempotente.

**À prévoir :** idempotence métier par identifiant stable, clé fournisseur lorsque disponible, résultat externe conservé, leases renouvelables ou durée adaptée, et rapprochement après succès externe suivi d'une panne locale.

## 2. Notifications et outbox

### Contrat de déduplication incohérent

`NotificationService.queue()` ne cherche en mémoire que les doublons `PENDING`. La migration `011_v611_notification_outbox.sql` impose `UNIQUE(organization_id, dedupe_key)` sans condition de statut. `PostgresApiRepository.create_notification()` utilise `ON CONFLICT ... DO NOTHING`, sans renvoyer la notification déjà persistée ni signaler le conflit.

Après un envoi ou une annulation, une nouvelle demande de notification identique peut donc passer le contrôle mémoire, être ignorée par PostgreSQL, puis rester dans le store local avec un nouvel identifiant sans ligne correspondante en base. Il faut décider si la déduplication est permanente, limitée dans le temps ou limitée aux états actifs, puis aligner le service et le schéma.

### Worker PostgreSQL : transaction ouverte pendant le réseau

`PostgresNotificationWorker.run_once()` sélectionne les lignes `PENDING` avec `FOR UPDATE SKIP LOCKED`, puis appelle `delivery_func` dans la même transaction avant de mettre à jour le statut.

Le verrou SQL reste donc détenu pendant SMTP/HTTP. Si le fournisseur accepte le message puis que le processus ou la transaction échoue avant commit, la ligne reste à traiter et un nouvel envoi est possible. Un transport lent retient aussi les verrous et la connexion.

**Architecture cible :** réservation courte et durable (état PROCESSING, propriétaire, bail, tentative), commit avant l'appel réseau, puis finalisation séparée. L'expiration du bail doit permettre une reprise explicite.

### Worker réellement utilisé par l'API

La route `POST /v1/notifications/worker/run` appelle `NotificationService.run_worker()`, qui charge les notifications en mémoire et exécute `NotificationWorker.run_once()`. Elle ne délègue pas à `PostgresNotificationWorker`.

Cette voie ne réserve pas atomiquement les lignes avant l'envoi. Plusieurs processus API peuvent lire la même notification PENDING et la livrer simultanément. Le worker PostgreSQL existe dans le dépôt, mais sa présence n'établit pas qu'il est raccordé au chemin d'exploitation.

`NotificationService.deliver()` présente aussi une fenêtre entre livraison fournisseur et sauvegarde de SENT. Le canal IN_APP correspond à un acquittement interne, pas à une preuve de lecture par le destinataire.

### Reprises et supervision

Le worker applicatif applique un backoff et borne les tentatives avec `max_attempts`. Le worker PostgreSQL applique aussi cette limite aux exceptions de livraison, et matérialise l'échec final par `dead_lettered_at` alors que le statut peut rester PENDING. Les vues et métriques doivent donc interpréter ce champ en plus du statut.

`scripts/worker.py` traite un seul job de traitement par invocation. Il importe `PostgresNotificationWorker` mais ne le lance pas. L'endpoint HTTP notification est réservé aux rôles OWNER/ADMIN ; il ne remplace pas un superviseur de worker de fond.

## 3. Google Pub/Sub et synchronisation

`AuthenticatedPubSubReceiver` exige un vérificateur injecté, parse l'événement puis appelle `claim_event_and_enqueue()`. Le reçu `google_processed_events` et l'insertion du job `background_jobs` sont dans la même transaction tenant-scoped ; la clé événement est aussi utilisée comme clé d'idempotence du job. Cela réduit le risque de double enqueue lors des retries Pub/Sub.

Le reçu est enregistré avant l'exécution du handler. Si un job est supprimé manuellement, mal configuré ou bloqué définitivement, le nouvel événement sera reconnu comme doublon et ne recréera pas le job. Il faut pouvoir rapprocher les reçus des jobs existants et de leur état terminal.

`GoogleSyncEngine` utilise par défaut la file SQLite `background_jobs`, alors que le récepteur Pub/Sub écrit dans la file PostgreSQL `background_jobs`. Ne pas supposer que le mapping des handlers du moteur est automatiquement assemblé au worker PostgreSQL de production.

La synchronisation paginée enregistre son curseur après les upserts d'une page. Une interruption peut entraîner une relecture ; les écritures d'avis doivent rester idempotentes. L'appel Google, les écritures SQL et le curseur ne forment pas une transaction atomique.

## 4. PayPal : point de risque prioritaire

La route `POST /v1/paypal/webhook` vérifie la signature avant de traiter l'événement. Elle appelle ensuite `billing_event_seen(event_id)`, qui cherche cet identifiant dans `billing_transactions.paypal_event_id`.

Pour un abonnement, la route persiste d'abord `paypal_event_id` sur la transaction. Elle met ensuite à jour le compte de facturation, insère un événement dans `billing_events` et écrit l'audit via des appels repository distincts. Ces écritures ne sont pas réunies dans une transaction atomique.

Si la transaction est sauvegardée puis que la mise à jour du compte ou l'insertion de l'événement échoue, le retry PayPal peut être immédiatement considéré comme doublon par `billing_event_seen()`. Le traitement sort alors avant de réparer les étapes secondaires. La demande de retry en cas d'échec de persistance de la transaction ne couvre pas cette fenêtre postérieure.

**Correction prioritaire :** registre webhook durable, unique par event_id, avec états reçus/en cours/terminés/en échec et étapes reprenables. Ne marquer terminé qu'après toutes les écritures locales nécessaires. Ajouter un rapprochement durable des événements vérifiés mais sans transaction locale correspondante : la route renvoie actuellement 200 même si aucun objet de facturation n'est trouvé.

Le parcours de confirmation d'abonnement appelle aussi PayPal avant d'enregistrer le ledger local. Le code signale qu'un abonnement peut avoir été créé sans être enregistré et qu'il n'est pas automatiquement annulé. Un mécanisme de rapprochement et une clé métier stable sont nécessaires pour éviter une deuxième création après un timeout ambigu.

## 5. Observabilité

- `processing_job_events` trace les transitions, tentatives, workers et identifiants de corrélation.
- `notification_observability.py` agrège états et événements d'audit ; ce n'est pas un détecteur autonome de jobs bloqués.
- Les événements d'audit et les statuts locaux ne prouvent pas à eux seuls la lecture d'un message ni la finalisation complète d'un effet fournisseur.
- Indicateurs à prévoir : âge du plus vieux pending, leases expirés, processing trop anciens, tentatives par type, jobs failed, notifications en retard, dead letters, durée/erreurs par fournisseur, webhooks PayPal non rapprochés et écarts entre reçus externes et ledger.

## 6. Plan de remédiation

### Priorité 0
1. PayPal : registre d'événements idempotent et reprise des étapes secondaires.
2. Notifications : réservation SQL courte avant réseau ; ne pas garder de transaction ouverte pendant SMTP/HTTP.
3. Notifications : raccorder le worker PostgreSQL au processus exploité ou supprimer l'ambiguïté entre les deux consommateurs.
4. Jobs : appliquer max_attempts également aux leases expirés.

### Priorité 1
5. Renouveler les leases ou définir une durée adaptée aux handlers longs.
6. Propager des clés d'idempotence métier aux fournisseurs et conserver les identifiants de leurs opérations.
7. Rapprocher les effets externes réussis dont la finalisation locale a échoué.
8. Aligner la déduplication de l'outbox avec la règle métier retenue.

### Priorité 2
9. Définir un superviseur permanent, son arrêt gracieux et ses variables d'exploitation.
10. Exposer alertes sur les âges, leases, retries, dead letters et événements non rapprochés.
11. Documenter la reprise manuelle sans rejouer aveuglément un effet externe.

## 7. Sources examinées

`src/background_jobs.py`, `src/processing_jobs.py`, `src/postgres_processing.py`, `src/postgres_sync.py`, `src/google_sync_engine.py`, `src/google_pubsub_receiver.py`, `src/notification_outbox.py`, `src/notification_service.py`, `src/notification_worker.py`, `src/postgres_notification_worker.py`, `src/notification_delivery.py`, `src/notification_observability.py`, `src/paypal_client.py`, `src/api_server.py`, `src/postgres_api_repository.py`, `scripts/worker.py`, `migrations/011_v611_notification_outbox.sql`, `migrations/012_v612_notification_delivery.sql`, `migrations/013_v613_notification_worker.sql`, `migrations/029_v643_processing_architecture.sql`.

## Conclusion

Les files et mécanismes de reprise sont présents, mais les frontières entre fournisseur externe et persistance locale exposent encore le système aux doubles exécutions ou aux reprises incomplètes. Le webhook PayPal, le worker PostgreSQL de notifications et la récupération des leases expirés sont les sujets à traiter en premier.

Ce lot est documentaire : aucun code runtime, schéma SQL ou donnée réelle n'a été modifié.
