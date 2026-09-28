from __future__ import annotations
import os
from pathlib import Path
import psycopg

ROOT=Path(__file__).resolve().parents[1]
MIGRATIONS=ROOT/"migrations"

def main() -> None:
    dsn=os.environ.get("DATABASE_URL","").strip()
    if not dsn:
        raise SystemExit("DATABASE_URL is required")
    files=sorted(MIGRATIONS.glob("*.sql"))
    with psycopg.connect(dsn) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for path in files:
            version=path.stem
            applied=conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version=%s",
                (version,),
            ).fetchone()
            if applied:
                continue
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations(version) VALUES (%s)",(version,))
        conn.commit()

if __name__=="__main__":
    main()
