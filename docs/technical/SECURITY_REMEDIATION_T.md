# Corrections de sécurité — lot T

Date : 2026-10-03  
Branche : `develop`  
Référence : audit du lot S, `SECURITY_API_DATA_AUDIT.md`.

## Corrections appliquées

### T-01 — Récupération de compte atomique

`PostgresAPIRepository.reset_password_with_recovery_token()` réalise dans une seule transaction :
- la consommation conditionnelle du token, seulement s'il n'est ni utilisé ni expiré ;
- la mise à jour du hash du mot de passe ;
- la révocation des sessions actives de l'utilisateur ;
- l'écriture de l'événement `PASSWORD_RECOVERED`.

La mise à jour du mot de passe annule la transaction si le compte lié au token n'existe plus. La route refuse le succès si le repository ne fournit pas cette opération atomique. Le mode mémoire sérialise la section finale avec le verrou de l'API et revérifie le token avant la mutation.

### T-02 — En-têtes de sécurité sur les réponses statiques

Les ressources frontend servies directement par WSGI, ainsi que `robots.txt` et `sitemap.xml`, réutilisent désormais `security_headers()` lorsque `SECURE_HEADERS` est actif. Les ressources statiques utilisent `Cache-Control: no-cache`.

### T-03 — Clé MFA et libellé de production

Le contrôle de présence de `REVIEW_DEFENSE_MFA_ENCRYPTION_KEY` utilise maintenant `self.config.production`, cohérent avec la configuration qui reconnaît `prod` et `production`.

### T-04 — Transport SMTP en production

Lorsque la récupération ou la vérification d'adresse est activée en production, le démarrage refuse `SMTP_STARTTLS=false`. L'adaptateur SMTP refuse également l'authentification SMTP si STARTTLS est désactivé.

## Constats du lot S non corrigés ici

| Constat | État | Motif |
|---|---|---|
| S-03 — Rate limiting distribué | À traiter | Nécessite un stockage partagé atomique et une décision d'infrastructure. |
| S-04 — Bearer token dans sessionStorage / CSP inline | À traiter | Nécessite une migration d'authentification et une politique CSRF coordonnée. |
| S-07 — Détection réelle des fichiers | À traiter | Nécessite une politique de formats et des parseurs isolés. |
| S-08 — Cycle de vie des clés | À traiter | Nécessite un processus de gestionnaire de secrets, rotation et restauration. |
| S-09 — Minimisation du payload PayPal | À traiter | Nécessite de définir les champs de rapprochement et les besoins de conservation. |

## Vérification statique

Relecture des blocs modifiés dans `src/api_server.py`, `src/postgres_api_repository.py`, `src/production_config.py` et `src/recovery_email.py`. Aucun test, build, typecheck, lint, workflow GitHub Actions, appel réseau applicatif ou accès à une base de données n'a été effectué.

Aucun changement n'a été apporté aux interfaces d'administration ni aux règles métier de traitement des avis.


Suite : consulter [SECURITY_REMEDIATION_U.md](./SECURITY_REMEDIATION_U.md)
pour les quotas partagés PostgreSQL et la validation des signatures de fichiers.
