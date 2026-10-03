# Infrastructure — zone de structuration

Ce répertoire accueille progressivement les éléments d'infrastructure, sans devenir immédiatement leur source d'exécution.

## Sources actives à préserver

- Entrée WSGI : `wsgi.py`.
- Démarrage production : `scripts/start_production.sh`.
- Contrôle pré-démarrage : `scripts/production_check.py`.
- Migrations réellement exécutées : `scripts/migrate.py`, qui lit actuellement `migrations/*.sql`.
- Configuration conteneur : `Dockerfile`, `docker-compose*.yml`, `Caddyfile`.
- Observabilité : `prometheus.yml`, `monitoring/alerts.yml`.
- Configuration applicative : `src/deployment.py`, `src/production_config.py`.

## Règle de migration

Les sous-répertoires ci-dessous sont des zones de destination et de documentation. Aucun fichier actif n'est déplacé ni dupliqué par cette étape. Toute migration ultérieure doit mettre à jour les chemins, imports, workflows et procédures de déploiement dans un changement atomique validé.
