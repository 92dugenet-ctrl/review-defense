#!/usr/bin/env python3
"""Fail-fast production configuration and dependency check."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.production_config import ProductionConfig
from src.deployment import DeploymentConfig


def main() -> int:
    try:
        config = ProductionConfig.from_env()
        config.validate_startup(require_database=True)
        deployment = DeploymentConfig.from_env()
        deployment.validate()
    except Exception as exc:
        print(f"production check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    required = ("DATABASE_URL",)
    missing = [key for key in required if not os.getenv(key, "").strip()]
    if missing:
        print("production check failed: missing " + ", ".join(missing), file=sys.stderr)
        return 1
    print("production configuration: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
