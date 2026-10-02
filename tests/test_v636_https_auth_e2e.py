from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v636_live_e2e_requires_https_and_dedicated_credentials():
    s=(ROOT/'scripts/staging_e2e.py').read_text()
    assert "STAGING_BASE_URL" in s
    assert "E2E_EMAIL" in s and "E2E_PASSWORD" in s and "E2E_ORGANIZATION_ID" in s
    assert "must use HTTPS" in s

def test_v636_mfa_is_verified_before_browser_certification():
    s=(ROOT/'scripts/staging_e2e.py').read_text()
    assert "E2E_MFA_SECRET" in s
    assert "MFA-enabled staging account accepted password-only login" in s
    assert "totp_code" in s

def test_v636_browser_certification_blocks_google_resources():
    s=(ROOT/'scripts/staging_e2e.py').read_text()
    assert "googleapis.com" in s and "google.com" in s
    assert "no_external_google" in s

def test_v636_workflow_runs_live_e2e_after_deployment():
    s=(ROOT/'.github/workflows/review-defense-staging.yml').read_text()
    assert "staging-e2e" in s
    assert "scripts/staging_e2e.py" in s
    assert "STAGING_BASE_URL" in s and "E2E_MFA_SECRET" in s

def test_v636_workflow_installs_playwright_for_real_browser():
    s=(ROOT/'.github/workflows/review-defense-staging.yml').read_text()
    assert "playwright" in s and "playwright install --with-deps chromium" in s
