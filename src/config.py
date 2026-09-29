from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, minimum: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if parsed < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}")
    return parsed


@dataclass(frozen=True)
class Settings:
    environment: str
    host: str
    port: int
    database_url: str
    secure_headers: bool
    db_connect_timeout: int


def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("REVIEW_DEFENSE_ENV", "development").strip() or "development",
        host=os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0",
        port=_env_int("PORT", 8080, 1),
        database_url=os.getenv("DATABASE_URL", "").strip(),
        secure_headers=_env_bool("SECURE_HEADERS", True),
        db_connect_timeout=_env_int("DB_CONNECT_TIMEOUT", 5, 1),
    )
