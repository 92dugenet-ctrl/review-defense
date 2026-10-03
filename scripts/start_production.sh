#!/bin/sh
set -eu

export HOST="${HOST:-0.0.0.0}"
export REVIEW_DEFENSE_ENV="${REVIEW_DEFENSE_ENV:-production}"

python scripts/production_check.py
python scripts/migrate.py

exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 60 \
    --access-logfile - \
    wsgi:app
