"""Compatibility entrypoint for eCloudServ's default Python runtime.

eCloudServ's generic Python image defaults to executing bot.py. Keep this
thin adapter so the platform can start Review Defense without changing the
application architecture: the actual WSGI application remains wsgi:app.
"""
from __future__ import annotations

import os
import sys


def build_gunicorn_command(port: str | None = None) -> list[str]:
    selected_port = port or os.environ.get("PORT") or "8080"
    return [
        sys.executable,
        "-m",
        "gunicorn",
        "--bind",
        f"0.0.0.0:{selected_port}",
        "--workers",
        "2",
        "--threads",
        "4",
        "--timeout",
        "60",
        "wsgi:app",
    ]


if __name__ == "__main__":
    os.execv(sys.executable, build_gunicorn_command())
