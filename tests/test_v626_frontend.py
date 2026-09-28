from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v626_frontend_has_production_auth_and_case_workflow():
    html = (ROOT / "frontend/index.html").read_text()
    js = (ROOT / "frontend/assets/app.js").read_text()
    css = (ROOT / "frontend/assets/app.css").read_text()
    assert "/assets/app.js" in html
    for route in ["/v1/auth/login", "/v1/auth/recovery/request", "/v1/auth/recovery/reset", "/v1/auth/email-verification/verify", "/v1/auth/mfa/confirm"]:
        assert route in js
    for route in ["/v1/cases/", "/evidence-matrix", "/review-readiness", "/decision", "/freeze", "/approve", "/submit"]:
        assert route in js
    assert "localStorage" in js
    assert "googleapis.com" not in js
    assert "google.com" not in js
    assert "fetch(\"https://" not in js
    assert "fetch('https://" not in js
    assert "grid-template-columns" in css


def test_v626_frontend_escapes_api_values_and_human_gates_actions():
    js = (ROOT / "frontend/assets/app.js").read_text()
    assert "const esc=" in js
    assert "onclick=\"createDecision" in js
    assert "confirm('Figer le dossier" in js
    assert "confirm('Confirmer l’approbation humaine" in js
    assert "Aucune action externe ne sera exécutée" in js


def test_v626_frontend_does_not_embed_credentials_or_external_submission_urls():
    root = ROOT / "frontend"
    for path in root.rglob("*"):
        if path.is_file():
            text = path.read_text(errors="ignore")
            assert "SMTP_PASSWORD" not in text
            assert "DATABASE_URL" not in text
            assert "OPENAI_API_KEY" not in text
            assert "googleapis.com" not in text


def test_v626_auth_pages_support_mfa_recovery_and_verification():
    js = (ROOT / "frontend/assets/app.js").read_text()
    assert "mfa_code" in js
    assert "one-time-code" in js
    assert "reset-password" in js
    assert "verify-email" in js
    assert "organization_id" in js
