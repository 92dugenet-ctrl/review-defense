# Cartographie d'extraction des domaines backend — 3 octobre 2026

## Objet et périmètre

Cette note décrit l'état réel de la séparation entre `src/` (code actuellement chargé par l'application) et `backend/` (organisation cible par domaines). Elle prépare les prochaines extractions sans modifier le runtime.

Référence : branche `develop`, commit parent `7e4d632df5199d683ffcc3744d46930108577e0d`.

Aucun fichier Python actif n'est déplacé, remplacé ou supprimé dans cette étape. Aucune route, migration, configuration serveur, intégration ou donnée n'est modifiée.

## 1. Constat d'exécution

- `wsgi.py` importe `create_app` depuis `src.api_server`.
- `src/api_server.py` importe ses services, modèles et adaptateurs via des imports relatifs à `src`.
- La composition HTTP, l'authentification, l'autorisation, l'orchestration et la sérialisation restent dans `src.api_server.py`.
- Les modules `backend/*` ne sont pas chargés par le point d'entrée WSGI du seul fait de leur présence.
- Plusieurs fichiers de `backend/` reproduisent des modules de `src/`; leur présence ne prouve ni leur activation ni leur indépendance.

Conséquence : `src/` reste la source runtime. `backend/` est une organisation cible et une zone de migration progressive, pas une deuxième implémentation à activer en parallèle.

## 2. Inventaire des domaines

| Domaine cible | Sources runtime observées | Organisation cible observée | État / précaution |
|---|---|---|---|
| API / composition | `src/api_server.py`, `src/app.py`, `src/app_shell.py` | `backend/api/` | Composition active dans `src`; le miroir API ne doit pas remplacer WSGI. |
| Identité / authentification | `src/identity.py`, `src/identity_repository.py`, `src/mfa.py`, `src/recovery_email.py`, `src/security_hardening.py` | `backend/authentication/` | Dépendances partagées avec sessions, rôles, sécurité et API; extraction distincte nécessaire. |
| Avis / Google | `src/review_workspace.py`, `src/case_review.py`, `src/case_review_matrix.py`, `src/case_review_service.py`, `src/google_*.py`, `src/review_queue.py`, `src/review_sla.py` | `backend/reviews/` | Le nom « reviews » recouvre avis Google et services de revue de dossiers; clarifier la propriété métier avant extraction. |
| Dossiers / Cases | `src/case_*.py`, `src/escalation_workflow.py`, `src/decision_workspace.py`, `src/submission_workspace.py`, `src/outcome_workspace.py`, `src/operations_ui.py` | `backend/cases/` | Domaine le plus avancé en services dédiés, mais routes et orchestration restent couplées à l'API. |
| Analyse / contradictions | `src/contradiction_*.py`, `src/evidence_extraction.py`, `src/evidence_ocr.py`, `src/policy_workspace.py` | `backend/analysis/` | Croise Cases, Reviews et Evidence; contrats inter-domaines à fixer. |
| Documents / preuves | `src/evidence_vault.py`, `src/evidence_extraction.py`, `src/evidence_ocr.py` | `backend/documents/` (README seulement dans l'inventaire) | Le code d'exécution reste dans `src`; stockage objet et intégrité sont sensibles. |
| Notifications | `src/notification_*.py`, `src/postgres_notification_worker.py`, `src/alert_workspace.py`, `src/ops_alerts.py` | `backend/notifications/` | Séparer création, politique, livraison, worker et observabilité; préserver l'outbox. |
| Facturation | `src/billing.py`, `src/billing_catalog.py`, `src/billing_service.py`, `src/paypal_client.py` | `backend/billing/` | PayPal et webhooks doivent rester derrière l'adaptateur Billing. |
| Organisations / permissions / utilisateurs | responsabilités partagées dans `src/api_server.py`, `src/identity.py` et repository | `backend/organizations/`, `backend/permissions/`, `backend/users/` | Répertoires documentaires sans implémentation autonome identifiée dans l'inventaire. |
| Persistance / plateforme | `src/postgres_*.py`, `src/database.py`, `src/deployment.py`, `src/production_config.py`, `src/observability.py`, `src/resilience.py` | principalement `backend/api/` | Ne pas confondre adaptateurs d'infrastructure et API; chemins de déploiement inchangés. |

## 3. Dépendances structurantes confirmées

### Composition API

`wsgi.py → src.api_server.create_app → ReviewDefenseAPI`

`src.api_server.py` importe directement les modules de domaines et les adaptateurs PostgreSQL/PayPal/Google. Il reste donc un composition root transversal. Une extraction doit commencer par des contrats de service stables, pas par un déplacement de fichiers.

### Cases

Le contrat architectural existant retient déjà le chargement du contexte Case comme premier seam : Case + Review + Evidence + Evidence Facts, avec `organization_id` et `case_id`. Les responsabilités HTTP, autorisation, décisions, notifications et intégrations doivent rester hors de ce seam.

Les services Cases déjà présents incluent notamment lifecycle, workspace, décision, soumission, approbation, matrice Evidence, opérations, escalade, SLA, revue et contradictions. Leur existence réduit le besoin de créer de nouveaux services, mais ne prouve pas que tous sont autonomes ou correctement câblés.

### Persistance

`src.api_server.py` garde un `MemoryStore` transversal et appelle directement le repository dans plusieurs parcours. La migration vers des services doit préserver les clés organisationnelles et les effets existants (audit, idempotence, persistance, événements).

## 4. Anomalies et blocages à lever avant activation

### 4.1 Copies de modules dans backend

Les fichiers miroirs ne sont pas une preuve de migration terminée. Certains imports relatifs semblent viser des modules qui ne sont pas présents dans le même package cible. Exemple observé : `backend/cases/case_lifecycle_service.py` importe `.security_hardening`, alors que le module de sécurité est organisé dans `backend/authentication/`. Même risque à examiner dans d'autres copies.

Règle : ne pas activer un miroir avant audit de tous ses imports relatifs/absolus, des dépendances transitives et des consommateurs.

### 4.2 Hydratation du contexte Case — isolation

Le code actuel de `CaseService.hydrate_context` dans `src/case_service.py` charge les lignes Evidence et Evidence Facts pour un `organization_id`, puis construit des listes filtrées uniquement par organisation. Ces listes ne sont pas explicitement restreintes au `case_id` demandé.

Même si les clés de stockage contiennent des identifiants, le résultat retourné peut inclure des éléments d'autres dossiers de la même organisation. Ce comportement doit être corrigé et couvert par des tests d'isolation par dossier et par organisation avant tout raccordement de cette méthode à une route.

### 4.3 Ambiguïté Reviews / Cases

`backend/reviews/` contient aussi des services de checklist de dossier. Avant extraction, distinguer :
- avis Google et représentation de l'avis ;
- revue/contrôle opérationnel d'un dossier ;
- checklist et readiness du dossier.

La propriété de chaque contrat doit être explicite pour éviter les dépendances circulaires.

## 5. Séquence d'extraction proposée

| Ordre | Travail | Livrable / critère d'entrée |
|---|---|---|
| A | Audit statique des imports de chaque miroir backend | Graphe importé, modules manquants, cycles, consommateurs et écarts src/backend. |
| B | Corriger et tester l'isolation du seam Case | Evidence et facts filtrés par organisation ET dossier; tests négatifs inter-dossiers et inter-organisations. |
| C | Définir le contrat de chargement Case | Entrée explicite `organization_id + case_id`; résultat typé; aucun effet métier non requis. |
| D | Raccorder le seam à un seul parcours de lecture Case | Contrat HTTP strictement identique; autorisation toujours côté serveur. |
| E | Exécuter la suite ciblée puis complète | Tests API, persistence, sécurité, isolation, workspace et non-régression verts avant commit runtime. |
| F | Extraire les transitions une par une | SLA, checklist, contradictions, décision, approbation puis soumission; un changement atomique à la fois. |

## 6. Invariants non négociables

- `wsgi.py` et `src.api_server.create_app` restent l'entrée active jusqu'à une migration explicitement validée.
- Aucun changement de ports, commandes de démarrage, variables de production ou configuration conteneur.
- Aucun changement de routes, méthodes HTTP, statuts, payloads JSON ou enveloppes d'erreur.
- Aucun changement de rôles, autorisations, isolation organisationnelle ou périmètre des dossiers.
- Aucune migration SQL ni modification de schéma dans une extraction de code.
- Aucun changement des intégrations Google, PayPal, SMTP, stockage Evidence ou workers.
- Pas de double source de vérité entre `src/` et `backend/`.
- Pas de suppression d'une source historique avant preuve d'absence de consommateurs et validation du remplacement.

## 7. État de cette étape

- Cartographie documentaire créée.
- Aucun code runtime modifié.
- Aucun test ni build n'a été exécuté dans cette étape.
- La prochaine modification de code doit commencer par le correctif d'isolation de `CaseService.hydrate_context`, accompagné de tests dédiés; elle ne doit pas activer les copies `backend/` en bloc.
