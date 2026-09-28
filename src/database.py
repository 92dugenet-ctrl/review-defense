from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator
import psycopg
@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    dsn=os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is required")
    with psycopg.connect(dsn) as conn:
        yield conn
def check_connection() -> bool:
    try:
        with connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
