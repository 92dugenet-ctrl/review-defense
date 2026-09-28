"""V6.22 deterministic PostgreSQL migration runner with drift protection."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Callable

class MigrationError(RuntimeError):
    pass

def migration_files(directory: str | Path) -> list[Path]:
    root = Path(directory)
    files = sorted(root.glob("*.sql"))
    for path in files:
        if not path.stem.split("_", 1)[0].isdigit():
            raise MigrationError(f"migration filename must start with a number: {path.name}")
    return files

def migration_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def apply_migrations(connect_factory: Callable[[], object], directory: str | Path) -> list[str]:
    files = migration_files(directory)
    conn = connect_factory()
    applied: list[str] = []
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                # Prevent two application instances from migrating the same database concurrently.
                cur.execute("SELECT pg_advisory_xact_lock(hashtext('review_defense:migrations'))")
                cur.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, filename text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now(), checksum text)")
                cur.execute("ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum text")
                cur.execute("SELECT version, filename, checksum FROM schema_migrations")
                raw_done = cur.fetchall()
                done = {}
                for row in raw_done:
                    # Backward-compatible with lightweight pre-V6.22 test doubles.
                    done[row[0]] = (row[0], row[1] if len(row) > 1 else None, row[2] if len(row) > 2 else None)
                for path in files:
                    version = path.name.split("_", 1)[0]
                    checksum = migration_checksum(path)
                    if version in done:
                        row = done[version]
                        if row[1] is not None and row[1] != path.name:
                            raise MigrationError(f"migration filename drift for {version}: database={row[1]} file={path.name}")
                        if row[2] and row[2] != checksum:
                            raise MigrationError(f"migration checksum drift for {path.name}")
                        if row[1] is not None and not row[2]:
                            cur.execute("UPDATE schema_migrations SET checksum=%s WHERE version=%s", (checksum, version))
                        continue
                    sql = path.read_text(encoding="utf-8")
                    if not sql.strip():
                        raise MigrationError(f"empty migration: {path.name}")
                    cur.execute(sql)
                    cur.execute("INSERT INTO schema_migrations(version, filename, checksum) VALUES (%s,%s,%s)", (version, path.name, checksum))
                    applied.append(path.name)
    except Exception as exc:
        raise MigrationError(f"migration failed: {exc}") from exc
    finally:
        conn.close()
    return applied
