# Cases — gestion des dossiers

## Responsabilité cible

Porter le cycle de vie d'un dossier, son espace de travail et les transitions métier : création, suivi, SLA, décision, approbation, escalade et soumission.

## Fichiers présents

- `case_service.py`, `case_lifecycle_service.py` : contexte et cycle de vie.
- `case_workspace_service.py`, `decision_workspace.py` : espace de travail et décision.
- `case_decision_service.py`, `case_approval_service.py` : décision et approbation.
- `case_submission_service.py`, `submission_workspace.py` : préparation et soumission.
- `case_escalation_service.py`, `escalation_workflow.py` : escalade.
- `case_sla_service.py`, `case_operations_service.py` : SLA et opérations.

## Dépendances et frontières

- Un dossier est toujours manipulé dans le contexte de son organisation.
- Les preuves et faits associés doivent être limités au couple `organization_id + case_id`.
- Les avis Google et leur ingestion relèvent du domaine Reviews; l'analyse spécialisée relève d'Analysis.
- Les routes, autorisations, notifications et adaptateurs de persistance restent des dépendances injectées, pas des effets implicites du service.

## Source exécutée

La composition actuelle importe les services depuis `src/`. Le dossier `backend/cases/` est la cible de classement, pas un remplacement activé.

## Règle d'extraction

Garder les contrats de lecture/écriture et les effets existants. Toute modification du périmètre d'un dossier doit être accompagnée de tests négatifs inter-dossiers et inter-organisations.
