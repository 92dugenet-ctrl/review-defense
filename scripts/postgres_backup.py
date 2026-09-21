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
    safe = urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
    return safe, {"PGPASSWORD": parsed.password}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    p.add_argument("--database-url", default=None, help="defaults to DATABASE_URL")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    dsn = args.database_url or os.getenv("DATABASE_URL")
    if not dsn:
        p.error("DATABASE_URL or --database-url is required")
    if args.output.exists() and not args.overwrite:
        p.error("output exists; pass --overwrite to replace it")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    safe_dsn, password_env = _dsn_without_password(dsn)
    env = os.environ.copy()
    env.update(password_env)
    result = subprocess.run(["pg_dump", "--format=custom", "--no-owner", "--file", str(args.output), safe_dsn], env=env, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
