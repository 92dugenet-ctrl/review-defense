# Reviews — avis et revue opérationnelle

## Responsabilité cible

Regrouper les avis Google, leur synchronisation et leur file de traitement, ainsi que les services de revue opérationnelle lorsqu'ils sont clairement identifiés comme tels.

## Fichiers présents

- `google_business_profile.py`, `google_integration.py` : profil et intégration Google.
- `google_pubsub_receiver.py`, `google_sync_engine.py` : réception d'événements et synchronisation.
- `review_workspace.py`, `review_queue.py`, `review_sla.py` : espace de travail, file et SLA des avis.
- `case_review.py`, `case_review_matrix.py`, `case_review_service.py` : revue/checklist liée aux dossiers.

## Frontière importante

Le terme « review » recouvre deux notions différentes :
- l'avis client Google et son cycle de synchronisation/traitement;
- la revue opérationnelle ou checklist d'un dossier.

Les modules `case_review_*` sont proches du domaine Cases. Leur présence ici est transitoire tant que la propriété du contrat n'est pas formellement décidée.

## Dépendances sensibles

Préserver les abonnements Google, la réception Pub/Sub, les jetons, les quotas, la synchronisation, l'association avis/organisation et les autorisations d'accès.

## Source exécutée

Les implémentations actives sont encore dans `src/`; ce dossier n'est pas chargé automatiquement par WSGI.
