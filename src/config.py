"""Configuration applicative historique, construite depuis l'environnement.

Ce module transforme des chaînes d'environnement en paramètres typés.
Il ne démarre pas le serveur et ne crée pas de connexion à la base : les
composants qui ont besoin de ces paramètres appellent get_settings().
La configuration de production détaillée est également portée par
src.production_config ; ne pas supposer que les deux objets sont interchangeables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    """Convertit une variable d'environnement en booléen avec valeur par défaut."""
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, minimum: int) -> int:
    """Lit un entier d'environnement et refuse les valeurs invalides ou trop basses."""
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
    """Valeurs d'exécution typées ; frozen évite leur mutation après création."""

    environment: str
    host: str
    port: int
    database_url: str
    secure_headers: bool
    db_connect_timeout: int


def get_settings() -> Settings:
    """Construit Settings à partir des variables disponibles dans le processus.

    Les valeurs par défaut sont des paramètres de développement. Les contrôles
    de production (HTTPS, proxy, secrets requis) sont gérés séparément par
    ProductionConfig et DeploymentConfig.
    """
    return Settings(
        environment=os.getenv("REVIEW_DEFENSE_ENV", "development").strip() or "development",
        host=os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0",
        port=_env_int("PORT", 8080, 1),
        database_url=os.getenv("DATABASE_URL", "").strip(),
        secure_headers=_env_bool("SECURE_HEADERS", True),
        db_connect_timeout=_env_int("DB_CONNECT_TIMEOUT", 5, 1),
    )
