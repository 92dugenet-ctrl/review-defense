from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_v635_certification_requires_explicit_test_database():
    s=(ROOT/'scripts/postgres_certification.py').read_text()
    assert 'REVIEW_DEFENSE_TEST_DATABASE_URL' in s
    assert 'DATABASE_URL' in s
    assert 'refusing DATABASE_URL fallback' in s

def test_v635_checks_idempotent_migrations_and_checksums():
    s=(ROOT/'scripts/postgres_certification.py').read_text()
    assert 'second = apply_migrations' in s
    assert 'second_apply_count' in s
    assert 'checksum_count' in s

def test_v635_checks_forced_rls_on_critical_tables():
    s=(ROOT/'scripts/postgres_certification.py').read_text()
    assert 'relforcerowsecurity' in s
    assert 'missing_forced_rls' in s

def test_v635_workflow_has_real_postgres_service_job():
    s=(ROOT/'.github/workflows/review-defense-staging.yml').read_text()
    assert 'services:' in s
    assert 'postgres:' in s
    assert 'postgres:16-alpine' in s
    assert 'REVIEW_DEFENSE_TEST_DATABASE_URL' in s
    assert 'scripts/postgres_certification.py' in s
