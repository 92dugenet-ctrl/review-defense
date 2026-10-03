#!/bin/sh
# Séquence unique de démarrage du conteneur de production.
# L'ordre est volontaire : arrêter le lancement si la configuration est
# invalide, mettre le schéma PostgreSQL à niveau, puis seulement démarrer WSGI.
set -eu

# Fournit les valeurs minimales attendues sans écraser celles injectées
# par Docker, Compose ou l'environnement d'hébergement.
export HOST="${HOST:-0.0.0.0}"
export REVIEW_DEFENSE_ENV="${REVIEW_DEFENSE_ENV:-production}"

# Étape 1 : vérification des prérequis (URL publique, DB, proxy, sécurité).
# En cas d'erreur, set -e interrompt immédiatement le script.
python scripts/production_check.py

# Étape 2 : applique migrations/*.sql et met à jour schema_migrations.
python scripts/migrate.py

# Étape 3 : remplace le shell par Gunicorn pour une gestion correcte des signaux.
# wsgi:app désigne l'objet app exposé dans le module racine wsgi.py.
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers "${GUNICORN_WORKERS:-${WEB_CONCURRENCY:-2}}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    wsgi:app
