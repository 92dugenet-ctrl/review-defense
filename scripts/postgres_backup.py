#!/usr/bin/env python3
"""Create a private PostgreSQL custom-format backup."""
from __future__ import annotations

# La sauvegarde PostgreSQL ne comprend pas le volume distinct des preuves.
# L'exploitation doit sauvegarder et protéger les deux périmètres séparément.

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
    parser.add_argument("output", type=Path)
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    dsn = args.database_url or os.getenv("DATABASE_URL")
    if not dsn:
        parser.error("DATABASE_URL or --database-url is required")

    output = args.output
    if output.is_symlink():
        parser.error("refusing to write through a symbolic link")
    if output.exists() and not args.overwrite:
        parser.error("output exists; pass --overwrite to replace it")

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        if not output.is_file():
            parser.error("output must be a regular file")
        os.chmod(output, 0o600)
    else:
        descriptor = os.open(
            output,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        os.close(descriptor)

    safe_dsn, password_env = _dsn_without_password(dsn)
    env = os.environ.copy()
    env.update(password_env)
    command = [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--file",
        str(output),
        safe_dsn,
    ]

    try:
        result = subprocess.run(command, env=env, check=False)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    if result.returncode != 0:
        output.unlink(missing_ok=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
