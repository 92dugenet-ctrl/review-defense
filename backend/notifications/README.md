# Notifications — événements et livraison

## Responsabilité cible

Gérer la politique de notification, la création des messages, leur mise en file, leur livraison, les workers et l'observabilité des envois.

## Fichiers présents

- `notification_service.py` : orchestration des notifications.
- `notification_policy.py` : règles de déclenchement et de ciblage.
- `notification_outbox.py` : outbox et persistance des messages à livrer.
- `notification_delivery.py` : livraison via les canaux configurés.
- `notification_worker.py`, `postgres_notification_worker.py` : traitement asynchrone.
- `notification_observability.py` : suivi et diagnostic.
- `alert_workspace.py`, `ops_alerts.py` : alertes opérationnelles.

## Dépendances sensibles

- Identifiant organisationnel et destinataires autorisés.
- Transaction métier et outbox pour éviter les pertes/doublons.
- Fournisseurs e-mail et configuration des canaux.
- Workers, reprise après erreur, idempotence et observabilité.

## Source exécutée

Le runtime actif utilise les modules correspondants de `src/`. Le dossier `backend/notifications/` reste une organisation cible.

## Règle d'extraction

Préserver l'ordre, l'idempotence, les tentatives, les statuts, les clés de corrélation et les garanties de l'outbox. Ne pas déplacer les workers ou changer leur mode de démarrage dans une simple étape de layout.
