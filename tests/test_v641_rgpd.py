from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_v641_rgpd_migration_contains_tenant_isolation():
    sql = (ROOT / "migrations" / "024_v641_rgpd_privacy_workflow.sql").read_text(encoding="utf-8")
    assert "privacy_requests" in sql
    assert "privacy_consents" in sql
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "app.organization_id" in sql
    assert "WITH CHECK" in sql


def test_v641_rgpd_api_exposes_rights_export_and_request_workflow():
    source = (ROOT / "src" / "api_server.py").read_text(encoding="utf-8")
    for route in (
        "/v1/privacy/export",
        "/v1/privacy/requests",
        "/v1/privacy/consents",
    ):
        assert route in source
    assert "PRIVACY_EXPORT_REQUESTED" in source
    assert "PRIVACY_REQUEST_CREATED" in source
    assert "PRIVACY_REQUEST_UPDATED" in source


def test_v641_rgpd_frontend_has_user_controls():
    source = (ROOT / "frontend" / "assets" / "app.js").read_text(encoding="utf-8")
    assert "downloadPrivacyExport" in source
    assert "createPrivacyRequest" in source
    assert "loadPrivacyAdmin" in source
