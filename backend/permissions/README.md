# Permissions — autorisations et politiques d'accès

## Responsabilité cible

Centraliser les décisions d'autorisation : rôles, capacités, politiques d'accès et vérifications sur les ressources, en tenant compte de l'organisation et du dossier concernés.

## État observé

Dossier réservé : aucun module Python d'implémentation n'est actuellement présent ici. Les vérifications actives sont encore réparties dans `src/api_server.py`, `src/identity.py` et les services appelés par l'API.

## Contrats à définir avant extraction

- Sujet : utilisateur authentifié et rôles effectifs.
- Tenant : organisation active et périmètre autorisé.
- Ressource : type, identifiant et organisation propriétaire.
- Action : lecture, création, modification, suppression ou transition métier.
- Décision : refus par défaut, résultat explicite et journalisation si requise.

## Règle de migration

Ne pas modifier les rôles, les règles d'accès ou les statuts HTTP dans une étape de classement. Les contrôles doivent rester côté serveur et être testés contre les accès inter-organisations et inter-dossiers.
