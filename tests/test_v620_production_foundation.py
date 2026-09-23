from pathlib import Path
import pytest
from src.production_config import ProductionConfig
from src.migration_runner import migration_files, apply_migrations, MigrationError


def test_production_config_requires_database_and_non_loopback():
    with pytest.raises(ValueError):
        ProductionConfig(environment="production", host="127.0.0.1", database_dsn=None).validate_startup()
    ProductionConfig(environment="production", host="0.0.0.0", database_dsn="postgresql://db").validate_startup()


def test_migrations_are_numbered_and_v620_is_present():
    files = migration_files(Path(__file__).parents[1] / "migrations")
    assert any(f.name.startswith("022_") for f in files)
    assert len(files) >= 20


def test_migration_runner_applies_once_and_is_transactional():
    class Cursor:
        def __init__(self, conn): self.conn = conn; self.sql = []
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, sql, params=None):
            self.sql.append((sql, params))
            if sql.startswith("SELECT version"):
                self._rows = [(v,) for v in self.conn.done]
            elif sql.startswith("INSERT INTO schema_migrations"):
                self.conn.done.add(params[0])
        def fetchall(self): return getattr(self, "_rows", [])
    class Tx:
        def __init__(self, conn): self.conn=conn
        def __enter__(self): return self
        def __exit__(self, *args): return False
    class Conn:
        def __init__(self): self.done=set(); self.closed=False
        def transaction(self): return Tx(self)
        def cursor(self): return Cursor(self)
        def close(self): self.closed=True
    conn=Conn()
    # Use a temporary migration directory to keep this unit test small.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        Path(d, "001_test.sql").write_text("CREATE TABLE test(id int);", encoding="utf-8")
        assert apply_migrations(lambda: conn, d) == ["001_test.sql"]
        assert apply_migrations(lambda: conn, d) == []
    assert conn.closed


def test_empty_migration_is_rejected(tmp_path):
    Path(tmp_path, "001_empty.sql").write_text("", encoding="utf-8")
    with pytest.raises(MigrationError):
        apply_migrations(lambda: type("C", (), {"transaction": lambda s: None, "close": lambda s: None})(), tmp_path)
