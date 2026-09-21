# Review Defense V6.4 — Case Workspace complet

V6.4 transforme la vue dossier en véritable poste de travail analyste, sans déplacer les contrôles de sécurité hors du serveur.

## Implémenté
- Endpoint tenant-scoped `GET /v1/cases/:id/workspace`.
- Vue agrégée du review, claims, policy signals, preuves liées, tâches de preuves, timeline d'audit, décision, snapshot et approbations.
- Détection des tâches de preuves manquantes à partir des exigences des policy signals.
- Indicateur explicite de nécessité de revue humaine.
- Timeline alimentée par les événements d'audit du dossier et des preuves.
- Affichage interactif du dossier depuis la console V6.3.
- Aucun tenant_id accepté depuis le navigateur pour contourner l'isolation.
- Aucun appel Google depuis le frontend.
- Aucune suppression/signalement/réponse automatique à Google.
- Les transitions décision/freeze/approval/submission restent protégées par RBAC et les contrôles serveur existants.
- Les hashes SHA-256 des preuves et snapshots restent visibles et vérifiables.

## Validation
La suite complète doit être exécutée avec `pytest -q` avant livraison.
