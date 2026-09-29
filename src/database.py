from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg

from .config import get_settings


def database_url() -> str:
    value = get_settings().database_url or os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    settings = get_settings()
    with psycopg.connect(database_url(), connect_timeout=settings.db_connect_timeout) as conn:
        yield conn


def check_connection() -> bool:
    try:
        with connection() as conn:
            conn.execute("SELECT 1")
        return True
    except (Exception, psycopg.Error):
        return False
