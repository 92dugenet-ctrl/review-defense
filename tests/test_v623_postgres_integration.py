from pathlib import Path
import os
import pytest

ROOT = Path(__file__).parents[1]


def test_v623_live_integration_is_explicitly_opt_in():
    text = (ROOT / "src/postgres_integration.py").read_text(encoding="utf-8")
    assert "REVIEW_DEFENSE_TEST_DATABASE_URL" in text
    assert "os.getenv(\"DATABASE_URL\")" not in text


def test_v623_smoke_script_refuses_production_database_fallback():
    text = (ROOT / "scripts/postgres_smoke.py").read_text(encoding="utf-8")
    assert "refusing DATABASE_URL fallback" in text
    assert "apply_migrations" in text
    assert "V623_ROLLBACK" in text


def test_v623_backup_and_restore_are_explicit():
    backup = (ROOT / "scripts/postgres_backup.py").read_text(encoding="utf-8")
    restore = (ROOT / "scripts/postgres_restore.py").read_text(encoding="utf-8")
    assert "pg_dump" in backup
    assert "pg_restore" in restore
    assert "--confirm" in restore
    assert "--database-url" in restore


@pytest.mark.skipif(not os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL"), reason="live PostgreSQL integration not configured")
def test_v623_live_database_marker():
    from src.postgres_integration import IntegrationConfig, wait_for_database
    wait_for_database(IntegrationConfig.from_env(), attempts=1)


def test_v623_backup_strips_password_from_command_argument():
    namespace = {}
    source = (ROOT / "scripts/postgres_backup.py").read_text(encoding="utf-8")
    assert "PGPASSWORD" in source
    assert "_dsn_without_password" in source
    assert "--format=custom" in source
