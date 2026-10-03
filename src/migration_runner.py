"""PostgreSQL migration runner with filename and checksum drift protection."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable


class MigrationError(RuntimeError):
    """Raised when a migration cannot be applied safely."""


def migration_files(directory: str | Path) -> list[Path]:
    """Return SQL migrations ordered by their complete filename."""
    root = Path(directory)
    files = sorted(root.glob("*.sql"), key=lambda path: path.name)
    for path in files:
        if not path.stem.split("_", 1)[0].isdigit():
            raise MigrationError(
                f"migration filename must start with a number: {path.name}"
            )
    return files


def migration_checksum(path: Path) -> str:
    """Return the SHA-256 digest of a migration file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_migrations(
    connect_factory: Callable[[], object],
    directory: str | Path,
) -> list[str]:
    """Apply missing migrations using the same identity contract as startup."""
    files = migration_files(directory)
    conn = connect_factory()
    applied: list[str] = []

    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_advisory_xact_lock("
                    "hashtext('review-defense:migrations'))"
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version text PRIMARY KEY,
                        filename text,
                        applied_at timestamptz NOT NULL DEFAULT now(),
                        checksum text
                    )
                    """
                )
                cur.execute(
                    "ALTER TABLE schema_migrations "
                    "ADD COLUMN IF NOT EXISTS filename text"
                )
                cur.execute(
                    "ALTER TABLE schema_migrations "
                    "ADD COLUMN IF NOT EXISTS checksum text"
                )
                cur.execute(
                    "SELECT version, filename, checksum FROM schema_migrations"
                )
                done = {
                    row[0]: (row[1], row[2])
                    for row in cur.fetchall()
                }

                full_versions = {path.stem for path in files}
                legacy_prefixes = {
                    path.name.split("_", 1)[0] for path in files
                }
                ambiguous = sorted(
                    version
                    for version in done
                    if version in legacy_prefixes
                    and version not in full_versions
                )
                if ambiguous:
                    raise MigrationError(
                        "legacy numeric-only migration versions require "
                        "manual reconciliation before continuing: "
                        + ", ".join(ambiguous)
                    )

                for path in files:
                    version = path.stem
                    checksum = migration_checksum(path)
                    previous = done.get(version)

                    if previous is not None:
                        previous_filename, previous_checksum = previous
                        if (
                            previous_filename
                            and previous_filename != path.name
                        ):
                            raise MigrationError(
                                f"migration filename drift for {version}: "
                                f"database={previous_filename} "
                                f"file={path.name}"
                            )
                        if previous_checksum and previous_checksum != checksum:
                            raise MigrationError(
                                f"migration checksum drift for {path.name}"
                            )
                        if not previous_filename or not previous_checksum:
                            cur.execute(
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
                        raise MigrationError(f"empty migration: {path.name}")
                    cur.execute(sql)
                    cur.execute(
                        """
                        INSERT INTO schema_migrations(
                            version, filename, checksum
                        )
                        VALUES (%s, %s, %s)
                        """,
                        (version, path.name, checksum),
                    )
                    applied.append(path.name)
                    done[version] = (path.name, checksum)
    except Exception as exc:
        raise MigrationError(f"migration failed: {exc}") from exc
    finally:
        conn.close()

    return applied
