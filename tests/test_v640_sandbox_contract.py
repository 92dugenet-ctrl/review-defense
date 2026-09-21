from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "sandbox_seed.py").read_text(encoding="utf-8")


def test_sandbox_is_test_database_only():
    assert "REVIEW_DEFENSE_TEST_DATABASE_URL" in SCRIPT
    assert "DATABASE_URL" in SCRIPT
    assert "Refusing to use DATABASE_URL" in SCRIPT


def test_sandbox_contains_two_tenants_and_all_demo_roles():
    assert 'seed_tenant(cur, f"{PREFIX} Alpha", "alpha")' in SCRIPT
    assert 'seed_tenant(cur, f"{PREFIX} Beta", "beta")' in SCRIPT
    for role in ("OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER"):
        assert f'"{role}"' in SCRIPT


def test_sandbox_covers_human_gate_entities():
    for table in (
        "api_reviews",
        "api_cases",
        "api_evidence",
        "api_decisions",
        "api_dossier_snapshots",
        "api_approvals",
        "api_submissions",
        "contradiction_findings",
        "case_review_checklist",
        "notification_outbox",
        "security_events",
    ):
        assert f"INSERT INTO {table}" in SCRIPT


def test_sandbox_never_enables_external_submission():
    assert "external_call" in SCRIPT
    assert "VALUES(%s,%s,%s,'PREPARED',false)" in SCRIPT
    assert '"external_actions_enabled":false' in SCRIPT
