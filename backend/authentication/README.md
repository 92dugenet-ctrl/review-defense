# Authentication — identité et sécurité d'accès

## Responsabilité cible

Gérer l'identité des utilisateurs et les mécanismes d'authentification : identité, persistance associée, authentification multifacteur, récupération d'accès et protections de sécurité.

## Fichiers présents

- `identity.py` : services et règles d'identité.
- `identity_repository.py` : persistance liée à l'identité.
- `mfa.py` : authentification multifacteur.
- `recovery_email.py` : récupération par e-mail.
- `security_hardening.py` : contrôles et durcissement de sécurité.

## Dépendances sensibles

- Sessions, cookies, jetons et cycle de vie de connexion.
- Utilisateurs, organisations, rôles et permissions.
- Routes de connexion, inscription, vérification et récupération.
- Secrets, fournisseurs e-mail et configuration de production.

## Source exécutée

Les modules actifs sont encore importés depuis `src/` par la composition actuelle `src.api_server`. Ce dossier décrit la cible de migration; il ne remplace pas ces imports.

## Règle d'extraction

Ne pas déplacer l'identité sans cartographier tous les consommateurs et préserver à l'identique les contrats de session, les réponses d'authentification, les exigences MFA et les contrôles d'accès.
