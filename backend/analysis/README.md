# Analysis — analyse et qualification

## Responsabilité cible

Regrouper les moteurs d'analyse et de qualification : détection de contradictions, matrices de preuves, extraction/OCR, analyse de politiques et espaces analytiques.

## Fichiers présents

- `analytics_workspace.py`, `outcome_workspace.py`, `policy_workspace.py` : espaces analytiques.
- `contradiction_engine.py`, `contradiction_disposition.py`, `case_contradiction_service.py` : détection et traitement des contradictions.
- `case_evidence_matrix_service.py` : matrice de preuves d'un dossier.
- `evidence_extraction.py`, `evidence_ocr.py`, `evidence_vault.py` : extraction, OCR et coffre de preuves.
- `notification_policy.py` : politique de notification, responsabilité à confirmer avec Notifications.

## Frontières à clarifier

Les preuves et documents sont proches du domaine Documents; les contradictions et matrices dépendent de Cases; les politiques de notification relèvent potentiellement de Notifications. Ces fichiers sont regroupés ici de manière transitoire et ne doivent pas créer de dépendances circulaires.

## Source exécutée

Les implémentations actives restent dans `src/`. Ce dossier n'est pas chargé par le point d'entrée WSGI.

## Règle d'extraction

Définir des entrées/sorties explicites et typées. L'analyse ne doit ni contourner l'autorisation d'accès au dossier, ni élargir le périmètre des preuves à une autre organisation ou à un autre dossier.
