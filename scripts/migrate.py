"""Applique les migrations SQL versionnées à PostgreSQL.

Ce script est appelé au démarrage de production avant Gunicorn. Il lit
migrations/*.sql et enregistre les versions exécutées dans schema_migrations.
Les noms complets des fichiers sont les identifiants stables des migrations.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def database_url() -> str:
    """Récupère la chaîne de connexion sans secret par défaut."""
    value = os.environ.get("DATABASE_URL", "").strip()
    if not value:
        raise SystemExit("DATABASE_URL is required")
    return value


def migration_files() -> list[Path]:
    """Retourne les migrations dans l'ordre lexical de leur nom complet."""
    return sorted(MIGRATIONS.glob("*.sql"), key=lambda path: path.name)


def connect():
    """Ouvre PostgreSQL avec un délai de connexion borné."""
    return psycopg.connect(database_url(), connect_timeout=5)


def main() -> None:
    """Applique les migrations absentes et refuse les dérives détectables."""
    files = migration_files()

    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "ALTER TABLE schema_migrations "
            "ADD COLUMN IF NOT EXISTS filename TEXT"
        )
        conn.execute(
            "ALTER TABLE schema_migrations "
            "ADD COLUMN IF NOT EXISTS checksum TEXT"
        )

        # Même verrou que le runner historique pour sérialiser les migrations.
        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtext('review-defense:migrations'))"
        )
        rows = conn.execute(
            "SELECT version, filename, checksum FROM schema_migrations"
        ).fetchall()
        applied = {row[0]: (row[1], row[2]) for row in rows}

        for path in files:
            version = path.stem
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            previous = applied.get(version)

            if previous is not None:
                previous_filename, previous_checksum = previous
                if previous_filename and previous_filename != path.name:
                    raise RuntimeError(
                        f"migration filename drift for {version}: "
                        f"database={previous_filename} file={path.name}"
                    )
                if previous_checksum and previous_checksum != checksum:
                    raise RuntimeError(f"migration checksum drift for {path.name}")

                # Adoption contrôlée des entrées historiques sans empreinte.
                if not previous_filename or not previous_checksum:
                    conn.execute(
                        """
                        UPDATE schema_migrations
                        SET filename=%s, checksum=%s
                        WHERE version=%s
                        """,
                        (path.name, checksum, version),
                    )
                continue

            sql = path.read_text(encoding="utf-8")
            if not sql.strip():
                raise RuntimeError(f"empty migration: {path.name}")

            conn.execute(sql)
            conn.execute(
                """
                INSERT INTO schema_migrations(version, filename, checksum)
                VALUES (%s, %s, %s)
                """,
                (version, path.name, checksum),
            )

        conn.commit()


if __name__ == "__main__":
    main()
