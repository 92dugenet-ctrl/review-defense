#!/usr/bin/env python3
"""Contrôle bloquant de la configuration avant démarrage en production.

Ce script est appelé par start_production.sh avant les migrations et Gunicorn.
Il vérifie les contrats ProductionConfig et DeploymentConfig ainsi que la
présence explicite de DATABASE_URL. Il ne démarre aucun service.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Le script peut être lancé depuis n'importe quel répertoire : on ajoute
# la racine du dépôt au chemin d'import Python avant de charger src/.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.production_config import ProductionConfig
from src.deployment import DeploymentConfig


def main() -> int:
    """Retourne 0 si la configuration est cohérente, 1 sinon."""
    try:
        # Vérifie les variables métier et les prérequis de l'application.
        config = ProductionConfig.from_env()
        config.validate_startup(require_database=True)

        # Vérifie séparément l'URL publique et la confiance accordée au proxy.
        deployment = DeploymentConfig.from_env()
        deployment.validate()
    except Exception as exc:
        print(f"production check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    # Contrôle explicite du nom attendu par le script de migration PostgreSQL.
    required = ("DATABASE_URL",)
    missing = [key for key in required if not os.getenv(key, "").strip()]
    if missing:
        print("production check failed: missing " + ", ".join(missing), file=sys.stderr)
        return 1

    print("production configuration: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
