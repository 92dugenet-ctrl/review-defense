"""Applique les migrations SQL versionnées à PostgreSQL.

Ce script est appelé au démarrage de production avant Gunicorn. Il lit
migrations/*.sql, enregistre les versions exécutées dans schema_migrations
et utilise un verrou advisory PostgreSQL pour éviter deux migrations
simultanées lorsque plusieurs processus de déploiement démarrent.
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg

# Les chemins sont calculés depuis ce fichier, pas depuis le répertoire courant.
ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def database_url() -> str:
    """Récupère la chaîne de connexion sans jamais fournir de secret par défaut."""
    value = os.environ.get("DATABASE_URL", "").strip()
    if not value:
        raise SystemExit("DATABASE_URL is required")

    return value


def migration_files() -> list[Path]:
    """Retourne les migrations SQL dans l'ordre lexical de leur nom de fichier."""
    return sorted(MIGRATIONS.glob("*.sql"), key=lambda path: path.name)


def connect():
    """Ouvre PostgreSQL avec un délai de connexion borné."""
    return psycopg.connect(database_url(), connect_timeout=5)


def main() -> None:
    """Applique uniquement les migrations absentes du registre de schéma."""
    files = migration_files()

    with connect() as conn:
        # Registre durable : chaque nom de migration n'est enregistré qu'une fois.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Verrou transactionnel partagé par tous les lanceurs de migration du projet.
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('review-defense:migrations'))")

        for path in files:
            version = path.stem
            applied = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version=%s",
                (version,),
            ).fetchone()

            if applied:
                continue

            # Le SQL est exécuté puis sa version est inscrite dans la même transaction.
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_migrations(version) VALUES (%s)",
                (version,),
            )

        conn.commit()


if __name__ == "__main__":
    main()
