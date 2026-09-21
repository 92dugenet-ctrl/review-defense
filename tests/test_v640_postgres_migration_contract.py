from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"


def test_all_tenant_foreign_keys_target_canonical_organization_id():
    bad = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        if "REFERENCES organizations(organization_id)" in sql:
            bad.append(path.name)
    assert bad == []


def test_organizations_primary_key_is_created_before_tenant_migrations():
    initial = (MIGRATIONS / "001_initial.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS organizations" in initial
    assert "id uuid PRIMARY KEY" in initial


def test_updated_at_trigger_function_uses_valid_postgresql_dollar_quoting():
    sql = (MIGRATIONS / "020_v622_data_reliability.sql").read_text(encoding="utf-8")
    assert "LANGUAGE plpgsql AS $fn$" in sql
    assert "END;
$fn$;" in sql
    assert "AS $$fn$$" not in sql
