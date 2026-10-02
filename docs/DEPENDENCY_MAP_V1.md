# Review Defense — Dependency Map V1

## Purpose
Cette cartographie décrit la circulation actuelle du code avant toute refactorisation structurelle. Elle est descriptive et n'autorise aucun changement de comportement, de configuration serveur ou de schéma.

## 1. Flux global actuel
HTTP / Frontend → ReviewDefenseAPI.__call__() → ReviewDefenseAPI.handle() → authentification / autorisation / décodage → orchestration par route → modules métier → MemoryStore et/ou repository → PostgresAPIRepository → PostgresRepository / PostgreSQL.

External boundaries: Evidence → object storage/filesystem ; Billing → PayPal ; Notifications/recovery → email ; Reviews → intégrations Google ; Platform → configuration/telemetry/deployment.

## 2. Direction cible
HTTP → Application → Domain → Ports / Repository contracts → Infrastructure.
Cette séparation n'est pas encore complète. L'objectif est de réduire les croisements sans changer le comportement.

## 3. Identity & access
Modules: identity.py, security_hardening.py, mfa.py, recovery_email.py.
Flux principal: api_server → identity/security_hardening/mfa/recovery_email.
Règle: ces modules ne dépendent pas des contextes Cases, Evidence, Decisions ou Billing.

## 4. Reviews
Modules: review_workspace.py et intégrations Google.
Flux: api_server → review_workspace ; contradiction_engine → review_workspace.
Règle: Reviews possède la représentation et l'analyse des reviews. Les autres contextes consomment des contrats explicites.

## 5. Cases / Operations
Modules: case_review.py, case_review_matrix.py, review_queue.py, review_sla.py, escalation_workflow.py, operations_ui.py.
Flux: api_server orchestre ces modules et assemble actuellement reviews, evidence, contradictions, checklists et décisions.
Point de couplage majeur: le lifecycle Case n'est pas encore encapsulé derrière un service unique.
Règle: lifecycle, readiness, SLA et assignment appartiennent au contexte Cases.

## 6. Evidence
Modules: evidence_vault.py, evidence_extraction.py, evidence_ocr.py.
Flux: api_server → Evidence ; evidence_vault → security_hardening.
Règle: Evidence possède métadonnées, intégrité, extraction et OCR ; il ne possède pas la décision ou l'approbation.

## 7. Contradictions
Modules: contradiction_engine.py, contradiction_disposition.py.
Flux: api_server → contradiction_engine → review_workspace ; api_server → contradiction_disposition.
Règle: détection et disposition restent deux responsabilités distinctes ; la disposition reste une action humaine contrôlée.

## 8. Decisions / controlled submission
Modules: decision_workspace.py, submission_workspace.py, outcome_workspace.py.
Flux: api_server → decision_workspace.
Chaîne protégée: Decision → Freeze → Human Approval → Controlled Submission Preparation.
Règle: aucune route client ne contourne cette frontière.

## 9. Notifications
Modules: notification_outbox.py, notification_policy.py, notification_worker.py, notification_delivery.py, notification_observability.py.
Flux: api_server → outbox/policy/worker/observability ; worker → delivery + policy.
Règle: les modules métier demandent une notification ; ils n'appellent pas directement SMTP ou un transport externe.

## 10. Billing
Modules: billing_catalog.py, paypal_client.py.
Flux: api_server → billing_catalog / paypal_client → PayPal.
Règle: HTTP PayPal, credentials et détails de transport restent dans la frontière Billing/integration.

## 11. Persistence
Modules: postgres_api_repository.py, postgres_repository.py et intégrations PostgreSQL.
Flux: api_server → PostgresAPIRepository → PostgresRepository → PostgreSQL.
Couplage actuel: api_server décide encore directement quand appeler le repository et maintient un MemoryStore transversal.
Règle: les modules métier ne parlent jamais directement à PostgreSQL.

## 12. Cross-cutting infrastructure
security_hardening: sécurité partagée.
production_config: configuration.
observability: telemetry et health.
deployment: configuration HTTP/déploiement.
Ces modules ne doivent pas devenir une seconde couche métier.

## 13. Principaux points de fort couplage
1. ReviewDefenseAPI.handle(): routage, auth, validation, orchestration, état, repository, audit et réponses.
2. MemoryStore: état de nombreux bounded contexts dans une même structure.
3. Orchestration repository: les branches de routes décident directement de nombreuses écritures.
4. Case orchestration: les routes Cases assemblent plusieurs contextes métier.

## 14. Croisements interdits
Frontend → PostgreSQL ; Frontend → repository interne ; Frontend → credentials PayPal ; Domain → HTTP/WSGI ; Repository → HTTP/frontend ; Case domain → PayPal/SMTP/Google brut ; Review domain → implémentation DB ; Evidence domain → mutation de décision ; Client API → état administratif interne.

## 15. Méthode de refactorisation future
Un seul bounded context à la fois. Introduire une frontière service, déplacer l'orchestration hors de api_server.py, garder les repositories derrière cette frontière, réduire progressivement la part du MemoryStore, exécuter le workflow complet, attendre le vert, puis seulement commencer le commit suivant.

Le premier candidat d'extraction détaillée est Cases, car il traverse actuellement le plus grand nombre de responsabilités.

## 16. Vérification obligatoire
Chaque changement structurel devra préserver les routes, l'autorisation, le schéma DB, la configuration serveur et les intégrations externes, sans nouvelle dépendance interdite ni seconde source de vérité.

## 17. État figé
Cette cartographie correspond au baseline vert actuel. Elle ne modifie pas le runtime et n'autorise pas à elle seule une migration.