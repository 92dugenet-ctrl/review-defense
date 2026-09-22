from pathlib import Path

from src.security_hardening import PBKDF2_ITERATIONS, hash_password, verify_password


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


def test_e2e_provisioning_uses_application_password_hashing():
    assert "from src.security_hardening import hash_password" in SCRIPT
    assert "hash_password(password)" in SCRIPT
    assert "crypt(" not in SCRIPT
    assert "gen_salt(" not in SCRIPT
    assert "bcrypt" not in SCRIPT.lower()


def test_application_password_hash_contract_matches_provisioning():
    password = "V6.40-contract-password-123!"
    encoded = hash_password(password)

    scheme, iterations, salt_hex, digest_hex = encoded.split("$", 3)

    assert scheme == "pbkdf2_sha256"
    assert int(iterations) == PBKDF2_ITERATIONS == 310_000
    assert len(bytes.fromhex(salt_hex)) == 16
    assert len(bytes.fromhex(digest_hex)) == 32
    assert verify_password(password, encoded) is True
    assert verify_password("wrong-password-123!", encoded) is False
