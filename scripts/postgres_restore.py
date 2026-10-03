#!/usr/bin/env python3
"""Restore a PostgreSQL custom-format backup.

Destructive by design: --confirm and an explicit target are mandatory.
The target never defaults to the application's DATABASE_URL.
"""
from __future__ import annotations

# La restauration PostgreSQL ne restaure pas le volume distinct des preuves.
# Vérifier la sauvegarde de fichiers et la cible avant toute opération.

import argparse
import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def _dsn_without_password(dsn: str) -> tuple[str, dict[str, str]]:
    parsed = urlsplit(dsn)
    if parsed.scheme not in {"postgresql", "postgres"}:
        return dsn, {}
    if parsed.password is None:
        return dsn, {}

    user = parsed.username or ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{user}@{host}{port}" if user else f"{host}{port}"
    safe = urlunsplit(
        (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
    )
    return safe, {"PGPASSWORD": parsed.password}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    if not args.confirm:
        parser.error("--confirm is required because restore replaces database objects")
    if not args.backup.is_file() or args.backup.is_symlink():
        parser.error("backup must be an existing regular file")

    safe_dsn, password_env = _dsn_without_password(args.database_url)
    env = os.environ.copy()
    env.update(password_env)
    command = [
        "pg_restore",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--dbname",
        safe_dsn,
        str(args.backup),
    ]
    result = subprocess.run(command, env=env, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
