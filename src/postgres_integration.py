"""V6.23 PostgreSQL integration helpers.

These helpers are intentionally explicit: live integration checks must point at a
purpose-built test database. They never silently use the application's production
DATABASE_URL.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass


class PostgreSQLIntegrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class IntegrationConfig:
    dsn: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "IntegrationConfig":
        dsn = os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL", "").strip()
        if not dsn:
            raise PostgreSQLIntegrationError(
                "REVIEW_DEFENSE_TEST_DATABASE_URL is required for live PostgreSQL integration"
            )
        return cls(dsn=dsn, timeout_seconds=float(os.getenv("REVIEW_DEFENSE_TEST_DB_TIMEOUT", "10")))


def connect(config: IntegrationConfig):
    try:
        import psycopg
    except ImportError as exc:
        raise PostgreSQLIntegrationError("psycopg is required for live PostgreSQL integration") from exc
    try:
        return psycopg.connect(config.dsn, connect_timeout=max(1, int(config.timeout_seconds)))
    except Exception as exc:
        raise PostgreSQLIntegrationError(f"unable to connect to integration database: {exc}") from exc


def wait_for_database(config: IntegrationConfig, attempts: int = 12, delay_seconds: float = 1.0) -> None:
    last_error = None
    for _ in range(attempts):
        try:
            conn = connect(config)
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    if cur.fetchone()[0] == 1:
                        return
            finally:
                conn.close()
        except PostgreSQLIntegrationError as exc:
            last_error = exc
        time.sleep(delay_seconds)
    raise PostgreSQLIntegrationError(f"database did not become ready: {last_error}")
