# Users — cycle de vie utilisateur

## Responsabilité cible

Regrouper les opérations métier liées au compte utilisateur : profil, état du compte, préférences, rattachement organisationnel et cycle de vie, hors mécanismes d'authentification.

## État observé

Dossier réservé : aucun module Python d'implémentation n'est actuellement présent ici. Les responsabilités utilisateur sont encore réparties dans les modules d'identité et la composition API de `src/`.

## Frontière avec Authentication

- Users possède le profil et le cycle de vie métier du compte.
- Authentication gère les identifiants, sessions, MFA et récupération d'accès.
- Organizations gère le tenant et les appartenances.
- Permissions décide des actions autorisées.

## Règle de migration

Ne pas déplacer de logique tant que les contrats entre ces quatre domaines ne sont pas explicites. Préserver les identifiants, invitations, états de compte et règles de rattachement.
