"""Pterodactyl launcher for the Review Defense WSGI application."""
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    port = os.environ.get("SERVER_PORT", os.environ.get("PORT", "8000"))
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
