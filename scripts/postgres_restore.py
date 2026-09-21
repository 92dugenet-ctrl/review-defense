#!/usr/bin/env python3
"""Restore a PostgreSQL custom-format backup.

Destructive by design: --confirm is mandatory and the target must be explicitly
provided. Never defaults to the application's DATABASE_URL.
"""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("backup", type=Path)
    p.add_argument("--database-url", required=True)
    p.add_argument("--confirm", action="store_true")
    args = p.parse_args()
    if not args.confirm:
        p.error("--confirm is required because restore replaces database objects")
    if not args.backup.is_file():
        p.error(f"backup not found: {args.backup}")
    result = subprocess.run([
        "pg_restore", "--clean", "--if-exists", "--no-owner", "--dbname", args.database_url, str(args.backup)
    ], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
