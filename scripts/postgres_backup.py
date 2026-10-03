#!/usr/bin/env python3
"""Create a PostgreSQL custom-format backup without putting the password in argv."""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def _dsn_without_password(dsn: str) -> tuple[str, dict[str, str]]:
    parsed = urlsplit(dsn)
    if parsed.scheme not in {"postgresql", "postgres"} or parsed.password is None:
        return dsn, {}

    user = parsed.username or ""
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    auth = user
    netloc = f"{auth}@{host}{port}" if auth else f"{host}{port}"
    safe = urlunsplit(
        (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
    )
    return safe, {"PGPASSWORD": parsed.password}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--database-url",
        default=None,
        help="defaults to DATABASE_URL",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    dsn = args.database_url or os.getenv("DATABASE_URL")
    if not dsn:
        parser.error("DATABASE_URL or --database-url is required")

    if args.output.exists() and not args.overwrite:
        parser.error("output exists; pass --overwrite to replace it")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    safe_dsn, password_env = _dsn_without_password(dsn)
    env = os.environ.copy()
    env.update(password_env)

    command = [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--file",
        str(args.output),
        safe_dsn,
    ]
    result = subprocess.run(command, env=env, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
