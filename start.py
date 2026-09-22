"""eCloudServ launcher for the Review Defense WSGI application."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def load_env_file() -> None:
    """Load the container-local .env without overriding platform variables."""
    env_file = Path(".env")
    if not env_file.is_file():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]

        os.environ.setdefault(key, value)


def main() -> int:
    load_env_file()

    port = os.environ.get("SERVER_PORT", os.environ.get("PORT", "25875"))
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "--bind",
        f"0.0.0.0:{port}",
        "--workers",
        "2",
        "--threads",
        "4",
        "--timeout",
        "60",
        "wsgi:app",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
