from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator
import psycopg

def database_url() -> str:
    value=os.getenv("DATABASE_URL","").strip()
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value

@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url()) as conn:
        yield conn

def check_connection() -> bool:
    try:
        with connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
