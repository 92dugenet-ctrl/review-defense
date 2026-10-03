# Organizations — organisations et tenants

## Responsabilité cible

Porter le modèle d'organisation, son cycle de vie, ses paramètres et les règles de rattachement des ressources à un tenant.

## État observé

Dossier réservé : aucun module Python d'implémentation n'est actuellement présent ici. Les responsabilités d'organisation sont encore réparties dans la composition API, l'identité et les repositories de `src/`.

## Contrats à définir avant extraction

- Identifiant d'organisation et contexte tenant.
- Création, invitation, rattachement et désactivation.
- Propriété des utilisateurs, dossiers, avis, documents et abonnements.
- Isolation des requêtes et persistance.
- Interaction avec Permissions et Users.

## Règle de migration

Ne pas créer une seconde source de vérité ni déplacer les contrôles tenant hors des parcours actifs. Toute extraction doit préserver l'isolation organisationnelle sur les lectures comme sur les écritures.
