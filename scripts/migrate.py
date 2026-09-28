#!/usr/bin/env python3
from pathlib import Path
import os
from src.migration_runner import apply_migrations

def connect():
    import psycopg
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("REVIEW_DEFENSE_DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is required")
    return psycopg.connect(dsn)

if __name__ == "__main__":
    applied = apply_migrations(connect, Path(__file__).resolve().parents[1] / "migrations")
    print(f"Applied {len(applied)} migration(s): {', '.join(applied) if applied else 'none'}")
