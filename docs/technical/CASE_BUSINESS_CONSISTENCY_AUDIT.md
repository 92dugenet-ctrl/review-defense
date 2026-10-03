# Audit de cohérence métier des dossiers — lot Q

## Périmètre

Revue statique de `develop` : création/hydratation des dossiers, avis, preuves, faits extraits, contradictions, checklist, décisions, snapshots, approbations, soumissions, facturation, API et pages React.

Le runtime principal est documenté via WSGI et `src/api_server.py`. Les copies parallèles sous `backend/` ne sont pas présumées actives.

**Aucun test, build, typecheck, workflow, appel Google/PayPal ou accès à une base réelle n'a été effectué.** Aucun état métier ni aucune donnée réelle n'ont été modifiés. Les constats décrivent le code versionné, pas un environnement déployé.

## Synthèse

| Priorité | Constat | Risque |
|---|---|---|
| Critique | Les décisions/snapshots sont écrits mais ne sont pas rechargés par l'hydratation du dossier | Après redémarrage, dossier présent mais contexte décisionnel absent en mémoire |
| Critique | Le contrôle d'approbation compare le snapshot à son propre payload et non au dossier courant | Une décision peut rester approuvée après modification du contenu source |
| Élevée | Le snapshot ne comprend pas preuves, faits, contradictions/dispositions ni checklist | L'approbation ne couvre pas l'ensemble du contexte métier affiché |
| Élevée | Les écritures décision/snapshot/approbation/statut sont séparées | État partiel possible après erreur intermédiaire |
| Élevée | Décision DRAFT fait passer le dossier à ANALYZED | Statuts dossier et décision contradictoires |
| Élevée | `/submit` ne fait qu'enregistrer un brouillon local `external_call=False` | Préparation confondue avec soumission réelle |
| Élevée | Une mise à jour d'avis ne déclenche pas l'invalidation des décisions associées | Snapshot obsolète toujours approuvable |
| Moyenne | Les statuts PayPal et les statuts de classification de compte divergent | CANCELED/PAUSED/PAST_DUE/UNPAID peuvent être classés pending |

## 1. Cycle de vie du dossier

`POST /v1/cases` vérifie que l'avis existe dans l'organisation, puis appelle `CaseLifecycleService.create()`. La création est filtrée par organisation et écrit un événement `CASE_CREATED`.

Deux valeurs initiales coexistent :
- `Case.status` vaut `NEW` par défaut dans `src/case_service.py`.
- `CaseLifecycleService.create()` fixe explicitement `ANALYZING`.

Il n'existe pas de machine à états centrale ni de catalogue unique de transitions. Les services modifient directement `case.status` avec des chaînes de caractères.

| Opération | Statut dossier | Statut objet associé |
|---|---|---|
| Création | ANALYZING | — |
| Création décision | ANALYZED | Décision DRAFT |
| Gel | HUMAN_REVIEW | Décision PENDING_APPROVAL |
| Approbation | READY_TO_SUBMIT | Décision APPROVED |
| Préparation soumission | READY_TO_SUBMIT inchangé | Soumission DRAFT, external_call=false |

Le parcours observé ne fait pas évoluer le dossier vers `SUBMITTED`, `COMPLETED` ou `CLOSED`. Il ne faut donc pas interpréter l'endpoint `submit` comme une transmission effective.

Les gardes sont réparties : freeze vérifie surtout la présence d'un decision_id ; approve vérifie la présence d'un snapshot en mémoire puis le statut de décision ; submit vérifie APPROVED dans le service. Aucune politique de transition unique ne gouverne l'ensemble.

## 2. Avis source et invalidation

`POST /v1/reviews` effectue un upsert par organisation et identifiant d'avis. Un avis déjà utilisé par un dossier peut donc être modifié.

Le snapshot conserve une copie de l'avis au gel. En revanche, l'upsert d'avis ne recherche pas les dossiers associés et ne déclenche pas `invalidate_if_modified()`. Ce helper existe dans `src/decision_workspace.py`, mais le chemin observé de `CaseDecisionService.approve()` ne l'appelle pas et ne reconstruit pas le payload courant.

Une modification de l'avis après gel ou approbation peut donc laisser une décision existante sans invalidation automatique. Le snapshot garde l'ancienne photographie, mais la décision doit être explicitement invalidée ou versionnée lorsque sa source change.

## 3. Preuves, faits et contradictions

`CaseService.hydrate_context()` recharge les preuves et faits par organisation/dossier, puis contrôle les identifiants avant mise en cache. Les routes d'analyse vérifient également que les preuves sélectionnées appartiennent au dossier.

Le payload construit par `CaseDecisionService.freeze()` comprend :
- les champs du dossier ;
- l'avis ;
- les claims extraits ;
- les signaux de politique ;
- la décision.

Il n'inclut pas explicitement les preuves et leurs SHA-256, les faits extraits et leur vérification, les contradictions/dispositions, la checklist ni l'historique du dossier. Le hash du snapshot ne couvre donc pas la totalité du contexte présenté aux opérateurs.

La matrice `build_evidence_matrix()` relie les claims aux preuves et contradictions et conserve `requires_human_review=True`, mais cette vue n'est pas intégrée au payload figé par le service de décision.

## 4. Décision et approbation

Dans `approve_decision()`, le contrôle compare le hash de la décision au hash du snapshot et exécute `snapshot_matches(snapshot, snapshot.payload)`. Ce dernier contrôle recalcule le hash du payload déjà contenu dans le snapshot : il vérifie sa cohérence interne, pas sa correspondance avec les données courantes du dossier.

Le helper `invalidate_if_modified()` sait comparer le snapshot à un `current_payload`, mais le service d'approbation ne l'utilise pas.

Autre point : `CaseDecisionService.create()` génère une nouvelle décision sans vérifier qu'une décision non terminale existe déjà pour ce dossier. Le pointeur `case.decision_id` est remplacé par la dernière décision. Plusieurs décisions peuvent donc coexister sans règle explicite de versionnement, d'annulation ou d'archivage.

## 5. Persistance et redémarrage

Le repository expose les écritures `put_decision()`, `put_snapshot()`, `put_approval()`, `put_submission()`, ainsi que la lecture des approbations et soumissions.

Dans `src/postgres_api_repository.py`, aucun lecteur d'une décision individuelle ou d'un snapshot n'a été trouvé. `CaseService.hydrate_context()` recharge dossier, avis, preuves et faits, mais pas décision ni snapshot. `CaseDecisionService.freeze()` et `approve()` accèdent directement à `store.decisions` et `store.snapshots`.

Le workspace de dossier construit aussi sa liste d'approbations à partir de `store.approvals`. La route globale `GET /v1/approvals` sait utiliser le repository via `CaseApprovalService`, mais ce chargement n'est pas réinjecté dans le workspace du dossier.

Après redémarrage ou sur un autre processus API, le dossier peut donc être hydraté depuis PostgreSQL sans ses objets décisionnels associés en mémoire. Les opérations qui attendent ces objets peuvent échouer ou afficher un contexte incomplet malgré leur persistance SQL.

Les services modifient en outre le store mémoire avant plusieurs appels repository distincts :
- création : décision, puis dossier ;
- gel : snapshot, décision, puis dossier ;
- approbation : décision, approbation, puis dossier ;
- audit après les écritures.

Chaque méthode repository ouvre sa propre transaction. Une erreur intermédiaire peut laisser des données partielles et un cache plus avancé que la base.

## 6. Soumission

`CaseSubmissionService.prepare()` exige une décision APPROVED, crée un identifiant de soumission, enregistre `status=DRAFT` et fixe `external_call=False`. Le module indique explicitement qu'il ne réalise aucune soumission externe.

La route `POST /v1/cases/{id}/submit` appelle uniquement cette préparation locale et renvoie HTTP 201. Elle ne contacte pas Google et ne fait pas passer le dossier à SUBMITTED.

Le repository insère une nouvelle soumission sous un nouvel identifiant ; aucune unicité métier visible n'impose une seule soumission par décision/dossier. L'idempotence HTTP dépend de la clé transmise à `_idem()`, mais ne remplace pas une règle métier de versionnement.

La frontière externe est explicitement désactivée, ce qui est important à conserver. Il faut aligner les libellés API/interface sur « préparer la soumission » tant qu'aucun adaptateur externe n'est réellement appelé.

## 7. Google : résultat observé vs persistance

Dans `GoogleSyncEngine`, `ReviewCache.observe()` calcule un fingerprint et qualifie NEW/UPDATED/UNCHANGED. Puis `GoogleSyncEngine._record()` ajoute l'élément à `_results`, une collection en mémoire.

Dans ce moteur, `_record()` n'appelle pas `PostgresAPIRepository.upsert_review()`. Aucun raccordement direct de cette instance à `src/api_server.py` n'a été trouvé dans la revue. Cela ne prouve pas qu'aucun autre chemin n'enregistre les avis Google ; cela signifie que le moteur observé, seul, ne garantit pas leur persistance dans `api_reviews`. Le consommateur qui transfère ces résultats vers la persistance doit être identifié explicitement.

## 8. Facturation et droits

Deux vocabulaires coexistent :
- `src/billing.py` : TRIALING, ACTIVE, PAST_DUE, PAUSED, CANCELING, CANCELED, UNPAID.
- `src/billing_service.py` : actifs ACTIVE, COMPLETED, APPROVED, TRIALING ; terminaux CANCELLED, SUSPENDED, EXPIRED, PAYMENT_FAILED, DENIED, REVERSED, REFUNDED.

CANCELED, PAST_DUE, PAUSED, CANCELING et UNPAID ne figurent dans aucun de ces deux ensembles du helper. Ils tombent donc dans le cas `pending` de `account_status()`. Ce helper est utilisé lors de la confirmation d'abonnement et du traitement d'événements PayPal : l'écart doit être résolu avant de considérer pending comme une règle d'accès fiable.

Les politiques de plan et fonctionnalités sont aussi réparties entre `billing_catalog.py`, `billing_service.py` et `billing.py`. Il faut documenter leurs rôles ou établir une source de vérité unique pour les prix, limites et droits.

## 9. Interface

`CasesPage.tsx` affiche directement le statut retourné par l'API. `CaseDetailPage.tsx` affiche `workspace.state` et les états des preuves/tâches. L'interface ne calcule pas elle-même les transitions, ce qui est cohérent avec une API propriétaire des règles.

Le contrat TypeScript de la page détail ne décrit pas les objets décision, snapshot et approbation renvoyés par le workspace backend. Cette page ne représente donc pas à elle seule le cycle décisionnel complet. Les statuts bruts sont affichés sans dictionnaire central de libellés/transitions.

## 10. Plan de remédiation

### Priorité 0
1. Construire un payload canonique versionné : avis, preuves (IDs + SHA-256), faits vérifiés, contradictions/dispositions, checklist et éléments de décision.
2. À l'approbation, reconstruire le payload courant et comparer son hash au snapshot ; invalider si divergence.
3. Ajouter les lecteurs repository décision/snapshot et hydrater les décisions, snapshots et approbations au chargement d'un dossier.
4. Rendre atomiques ou réconciliables les écritures décision, snapshot, approbation, statut et audit.

### Priorité 1
5. Définir une machine à états centrale et les transitions autorisées.
6. Distinguer décision créée, dossier analysé, validation humaine, décision approuvée, soumission préparée et soumission réellement transmise.
7. Versionner/invalider les décisions quand l'avis, les preuves ou les faits changent.
8. Définir les règles d'unicité/versionnement des décisions et soumissions.

### Priorité 2
9. Aligner les statuts PayPal, états du compte et règles d'entitlement.
10. Identifier le consommateur qui persiste les avis issus du moteur Google.
11. Harmoniser les contrats de statut API/frontend.
12. Ajouter une procédure de rapprochement des dossiers dont la décision, le snapshot, l'approbation ou la soumission sont incomplets.

## 11. Fichiers examinés

`src/api_server.py`, `src/case_service.py`, `src/case_lifecycle_service.py`, `src/case_review_service.py`, `src/case_decision_service.py`, `src/case_submission_service.py`, `src/case_approval_service.py`, `src/case_operations_service.py`, `src/case_evidence_matrix_service.py`, `src/case_workspace_service.py`, `src/case_contradiction_service.py`, `src/case_review.py`, `src/case_review_matrix.py`, `src/decision_workspace.py`, `src/postgres_api_repository.py`, `src/postgres_repository.py`, `src/google_sync_engine.py`, `src/google_business_profile.py`, `src/billing.py`, `src/billing_service.py`, `frontend/src/pages/CasesPage.tsx`, `frontend/src/pages/CaseDetailPage.tsx`, `frontend/src/pages/BillingPage.tsx`, `migrations/015_v617_case_review.sql`, `migrations/017_v619_review_history_matrix.sql`, `migrations/023_v70_paypal_billing.sql`, `migrations/030_v644_billing_account_state.sql`.

## Conclusion

Le cycle de dossier est actuellement une succession de services et d'écritures plutôt qu'une machine à états entièrement cohérente. Les risques dominants sont l'absence de rechargement du contexte décisionnel depuis la persistance et l'approbation qui ne vérifie pas que le dossier courant correspond toujours au snapshot. La soumission reste une préparation locale, et les vocabulaires de facturation divergent.

Ce lot est documentaire : aucun changement runtime, aucune migration et aucune opération sur des données réelles.
