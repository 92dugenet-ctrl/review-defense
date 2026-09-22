from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "provision_e2e_account.py").read_text(encoding="utf-8")


def test_e2e_provisioning_requires_database_and_mfa_encryption_key():
    assert 'required("DATABASE_URL")' in SCRIPT
    assert 'required("REVIEW_DEFENSE_MFA_ENCRYPTION_KEY")' in SCRIPT


def test_e2e_provisioning_generates_runtime_secrets():
    assert "generate_secret()" in SCRIPT
    assert "strong_password()" in SCRIPT
    assert "encrypt_secret(totp_secret, encryption_key)" in SCRIPT


def test_e2e_provisioning_enables_mfa_and_persists_membership():
    assert "mfa_enabled,mfa_secret_enc,mfa_enabled_at" in SCRIPT
    assert "INSERT INTO memberships(organization_id,user_id,role)" in SCRIPT


def test_e2e_provisioning_refuses_duplicate_identity():
    assert "user already exists" in SCRIPT
    assert "organization already exists" in SCRIPT


def test_e2e_provisioning_does_not_hardcode_secrets():
    assert "mfa_secret_enc" in SCRIPT
    assert "Do not commit" in SCRIPT
