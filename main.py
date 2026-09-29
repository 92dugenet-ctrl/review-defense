"""eCloudServ-compatible entrypoint for the Review Defense WSGI application."""

from __future__ import annotations

import os
import sys


def build_gunicorn_command(port: str | int | None = None) -> list[str]:
    selected = str(port or os.environ.get("PORT") or "8080")
    return [
        sys.executable,
        "-m",
        "gunicorn",
        "--bind",
        f"0.0.0.0:{selected}",
        "--workers",
        os.environ.get("GUNICORN_WORKERS", "2"),
        "--threads",
        os.environ.get("GUNICORN_THREADS", "4"),
        "--timeout",
        os.environ.get("GUNICORN_TIMEOUT", "60"),
        "wsgi:app",
    ]


if __name__ == "__main__":
    os.execv(sys.executable, build_gunicorn_command())
