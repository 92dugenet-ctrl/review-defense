# Audit des suppressions et de l'intégrité référentielle — lot O

> Revue statique de `develop` au 3 octobre 2026. Aucune base n'a été interrogée, aucune donnée n'a été supprimée ou modifiée, et aucun test, build, typecheck ou workflow n'a été exécuté.

## Synthèse

Le schéma protège largement les données par organisation avec des clés étrangères vers `organizations` et des politiques RLS. Les suppressions d'organisation en base déclenchent plusieurs cascades. En revanche, le parcours applicatif ne présente pas de mécanisme général de suppression d'organisation, de compte, de dossier ou de preuve.

Le statut RGPD `ERASURE` est une demande métier : la route de mise à jour permet de passer une demande à `COMPLETED`, mais le code parcouru n'associe pas cette transition à une suppression effective des lignes, des fichiers ou des sauvegardes. Il ne faut donc pas assimiler le statut à une preuve d'effacement.

Aucune migration destructive n'est ajoutée dans ce lot : les contraintes existantes et les données potentiellement déjà déployées doivent être inventoriées avant de modifier les règles de suppression.

## 1. Parcours applicatif constaté

### Routes et repositories

- Dans `src/api_server.py`, les routes de confidentialité couvrent export, création, lecture et mise à jour des demandes, ainsi que lecture et enregistrement des consentements.
- La route `PATCH /v1/privacy/requests/{id}` accepte notamment le statut `COMPLETED`. Elle met à jour le statut et la note de réponse ; elle ne déclenche pas de suppression de compte, de dossier, de ligne métier ou d'objet de stockage.
- Aucun handler HTTP `DELETE` n'a été identifié dans le routeur API principal inspecté.
- `src/identity_repository.py` expose des opérations de mise à jour de mot de passe, révocation de sessions, rôles, invitations et MFA ; aucun parcours de suppression physique d'utilisateur ou d'organisation n'y apparaît.
- `src/postgres_repository.py` expose la création, la lecture et la mise à jour des demandes de confidentialité, mais pas de méthode de suppression ou de purge.
- `src/postgres_api_repository.py` supprime des états OAuth expirés ou consommés ; ce sont des suppressions techniques ciblées, pas un mécanisme général de purge métier.

### Conséquence

Les suppressions observées dans le code concernent principalement les états OAuth. Le cycle de vie des comptes, organisations, dossiers et preuves ne possède pas encore de service applicatif central qui orchestre les dépendances SQL et le stockage de fichiers.

## 2. Relations SQL et effets de suppression

### Relations d'organisation

Plusieurs tables tenant-scoped référencent `organizations(id)` avec `ON DELETE CASCADE`, notamment :

- `memberships`, `cases`, `case_events` et `api_sessions` ;
- les principales tables `api_*` de persistance ;
- les demandes et consentements de confidentialité ;
- les invitations, états OAuth, jetons de récupération et de vérification ;
- les connexions Google, documents client, paramètres, tâches de traitement et tables de facturation.

Une suppression SQL d'une organisation peut donc entraîner une suppression en cascade de nombreuses lignes. Elle ne supprime pas automatiquement les fichiers du volume d'évidence ou les objets externes référencés par `object_key`.

### Relations utilisateur qui bloquent ou modifient la suppression

| Table / colonne | Règle SQL observée | Effet sur la suppression d'un utilisateur |
|---|---|---|
| `memberships.user_id` | `ON DELETE CASCADE` | Supprime l'appartenance |
| `api_sessions.user_id` | `ON DELETE CASCADE` | Supprime les sessions |
| `password_recovery_tokens.user_id` | `ON DELETE CASCADE` | Supprime les jetons de récupération |
| `email_verification_tokens.user_id` | `ON DELETE CASCADE` | Supprime les jetons de vérification |
| `privacy_consents.user_id` | `ON DELETE CASCADE` | Supprime les consentements |
| `privacy_requests.requester_user_id` | `ON DELETE RESTRICT` | Peut bloquer la suppression du compte |
| `case_events.actor_user_id` | Référence sans action `ON DELETE` explicite | Le comportement par défaut `NO ACTION` peut bloquer la suppression |
| `organization_invitations.invited_by` | Référence sans action `ON DELETE` explicite | Peut bloquer la suppression du compte invitant |
| `client_documents.created_by` | Référence sans action `ON DELETE` explicite | Peut bloquer la suppression du créateur |
| `google_connections.created_by` | Référence sans action `ON DELETE` explicite | Peut bloquer la suppression du créateur |
| `security_events.actor_user_id`, `target_user_id` | `ON DELETE SET NULL` | Préserve l'événement en détachant l'identité |
| `billing_transactions.user_id` | `ON DELETE SET NULL` | Préserve la transaction en détachant l'utilisateur |

Les règles exactes dépendent de l'ensemble des contraintes effectivement appliquées dans chaque base. Le tableau décrit les définitions SQL présentes dans le dépôt, pas l'état d'une base déployée.

## 3. Références métier sans clé étrangère

Plusieurs colonnes d'identifiants métier sont déclarées sans clé étrangère correspondante dans les migrations examinées :

- `api_evidence.case_id` ne référence pas explicitement `api_cases` ou `cases`.
- `api_decisions.case_id`, `api_dossier_snapshots.case_id`, `api_approvals.case_id` et `api_submissions.case_id` ne possèdent pas de contrainte référentielle vers le dossier correspondant.
- `api_approvals.decision_id` n'a pas de clé étrangère vers `api_decisions`.
- `evidence_facts.evidence_id` et `evidence_facts.case_id`, ainsi que les références correspondantes dans `evidence_fact_suggestions`, sont stockées sans clé étrangère vers les objets parents.
- `contradiction_findings.case_id` et certaines références de dispositions/historique sont des identifiants métier sans contrainte complète vers le dossier ou la disposition.
- `client_documents.object_key` référence le stockage externe par convention applicative, pas par clé étrangère SQL.
- `processing_job_events.job_id` référence bien `processing_jobs(job_id)`, mais la contrainte ne garantit pas à elle seule que les deux lignes portent le même `organization_id`.

Ces choix peuvent être intentionnels pour compatibilité ou pour découpler les flux. Ils impliquent toutefois que PostgreSQL ne peut pas, à lui seul, empêcher toutes les références orphelines ou incohérentes. Avant d'ajouter des contraintes, il faut vérifier les données existantes et décider quelles relations doivent être strictes, détachables ou conservées comme historique.

## 4. Preuves et documents : deux stockages, une seule identité métier

- Les métadonnées de preuve sont persistées dans `api_evidence`.
- Les octets sont stockés séparément par `ObjectStore`, notamment via `FilesystemObjectStore`.
- `ObjectStore.delete(...)` existe au niveau de l'adaptateur, mais aucun parcours central observé ne coordonne la suppression de l'objet, de la ligne `api_evidence`, des faits extraits et des références des dossiers.
- Les documents du hub client possèdent un `object_key` dans `client_documents`; aucune suppression coordonnée de la ligne et de l'objet correspondant n'a été identifiée dans les parcours examinés.

Une suppression SQL en cascade ne supprime donc pas automatiquement les octets. Inversement, supprimer d'abord un fichier peut laisser une ligne SQL qui le référence. La suppression doit être conçue comme un processus durable et reprenable, pas comme deux suppressions indépendantes.

## 5. Demandes RGPD et effacement effectif

Le type `ERASURE` fait partie des catégories acceptées. Les statuts disponibles sont `RECEIVED`, `IN_REVIEW`, `COMPLETED` et `REJECTED`.

La transition vers `COMPLETED` ne vérifie pas dans le code parcouru que les actions suivantes ont été effectuées :

- identification de toutes les données liées à la personne dans chaque organisation ;
- traitement des relations qui bloquent une suppression SQL ;
- effacement ou anonymisation des lignes métier et des journaux selon leur finalité ;
- suppression des preuves et documents dans le volume externe ;
- traitement des tâches asynchrones, notifications et intégrations en attente ;
- traitement des copies de sauvegarde selon leur calendrier de rétention ;
- conservation d'une preuve d'exécution qui ne réintroduit pas les données supprimées.

Le statut doit donc être interprété comme l'état administratif de la demande, et non comme une garantie technique d'effacement complet.

## 6. Architecture de suppression recommandée

Avant d'implémenter les suppressions physiques, établir un contrat commun avec les étapes suivantes :

1. **Demande et autorisation** : identifier le sujet, l'organisation, le périmètre demandé et les règles de conservation applicables.
2. **Inventaire** : établir les identifiants de toutes les lignes, fichiers, tâches, tokens et références externes concernés.
3. **Préparation** : enregistrer une opération de suppression durable avec un identifiant, un périmètre et un état reprenable.
4. **Neutralisation** : révoquer les sessions, tokens, accès et tâches susceptibles de recréer ou d'exposer les données.
5. **Suppression des objets** : supprimer les octets dans le stockage externe et enregistrer chaque résultat ; prévoir les reprises en cas d'échec.
6. **Suppression / anonymisation SQL** : appliquer les règles de conservation décidées, puis traiter les relations enfants dans un ordre maîtrisé.
7. **Vérification de cohérence** : rechercher les références restantes et les objets orphelins à partir de l'inventaire.
8. **Clôture** : marquer la demande comme terminée uniquement après la validation du périmètre attendu, avec une trace minimale de l'opération.

Une transaction PostgreSQL ne peut pas rendre atomique une suppression qui inclut un volume de fichiers ou un fournisseur externe. Un journal d'opération et des étapes idempotentes sont donc nécessaires.

## 7. Corrections différées et ordre de traitement

Les changements suivants sont volontairement différés car ils exigent une décision métier ou un état réel du schéma :

- Arbitrer les références d'audit : conserver l'identité, la remplacer par une valeur neutre, ou détacher l'acteur avec `SET NULL`.
- Arbitrer `privacy_requests.requester_user_id` : la contrainte `RESTRICT` protège l'historique, mais bloque la suppression physique du compte.
- Définir le sort de `case_events.actor_user_id`, `organization_invitations.invited_by`, `client_documents.created_by` et `google_connections.created_by`.
- Décider quelles références de dossier/preuve doivent devenir des clés étrangères composites incluant `organization_id`.
- Définir une stratégie de suppression de fichiers reprenable et une réconciliation périodique des objets SQL et fichiers.
- Définir l'anonymisation et la rétention des factures, transactions, événements de sécurité et traces d'audit.

Ne pas modifier directement une migration déjà publiée. Toute évolution de contraintes doit passer par une nouvelle migration additive, précédée d'un inventaire des contraintes et des données existantes sur chaque environnement.

## Périmètre de vérification

Lecture statique du routeur API principal, repositories identité et PostgreSQL, adaptateur de stockage des preuves et migrations SQL suivies dans Git. Aucun endpoint de suppression n'a été appelé. Aucune base, aucun volume, aucun objet externe et aucune donnée réelle n'ont été manipulés. Aucun test, build, typecheck ou workflow n'a été exécuté.
