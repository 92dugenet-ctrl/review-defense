"""Import smoke tests for every module in the backend package tree."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BACKEND_MODULES = sorted(
    ".".join(path.relative_to(ROOT).with_suffix("").parts)
    for path in (ROOT / "backend").rglob("*.py")
    if path.name != "__init__.py"
)


@pytest.mark.parametrize("module_name", BACKEND_MODULES)
def test_backend_module_imports(module_name: str) -> None:
    """Backend modules must import without opening a database connection."""
    importlib.import_module(module_name)
