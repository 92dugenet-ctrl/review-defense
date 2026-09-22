#!/usr/bin/env python3
"""V6.40 provisioning helper for a dedicated staging E2E account.

Creates one isolated organization + user, enables TOTP MFA, and stores the
encrypted TOTP secret in PostgreSQL. Secrets are generated at runtime and are
never written to the repository.

Required environment:
  DATABASE_URL
  REVIEW_DEFENSE_MFA_ENCRYPTION_KEY  (Fernet key already configured by the app)

Optional environment:
  E2E_EMAIL
  E2E_PASSWORD
  E2E_ORGANIZATION_NAME
  E2E_ROLE (default ADMIN)

The command prints the five values needed by GitHub Actions once. Redirecting
the output to a protected local file is recommended. Never commit that file.
"""
from __future__ import annotations

import argparse
import os
import secrets
import string
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.fernet import Fernet
from src.mfa import generate_secret, otpauth_uri, encrypt_secret
from src.security_hardening import hash_password


ROLES = {"OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER"}


def strong_password(length: int = 28) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default=os.getenv("E2E_EMAIL", "").strip())
    parser.add_argument(
        "--organization-name",
        default=os.getenv("E2E_ORGANIZATION_NAME", "Review Defense E2E"),
    )
    parser.add_argument("--role", default=os.getenv("E2E_ROLE", "ADMIN"))
    args = parser.parse_args()

    if args.role not in ROLES:
        raise SystemExit(f"invalid role: {args.role}")

    dsn = required("DATABASE_URL")
    encryption_key = required("REVIEW_DEFENSE_MFA_ENCRYPTION_KEY")

    try:
        Fernet(encryption_key.encode())
    except Exception as exc:
        raise RuntimeError("REVIEW_DEFENSE_MFA_ENCRYPTION_KEY is not a valid Fernet key") from exc

    email = args.email or "e2e@review-defense.invalid"
    password = os.getenv("E2E_PASSWORD", "").strip() or strong_password()
    organization_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    totp_secret = generate_secret()
    encrypted_secret = encrypt_secret(totp_secret, encryption_key)
    uri = otpauth_uri(totp_secret, email)

    import psycopg

    with psycopg.connect(dsn) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM users WHERE email=%s",
                    (email,),
                )
                if cur.fetchone():
                    raise RuntimeError(f"user already exists: {email}")

                cur.execute(
                    "SELECT 1 FROM organizations WHERE name=%s",
                    (args.organization_name,),
                )
                if cur.fetchone():
                    raise RuntimeError(
                        f"organization already exists: {args.organization_name}"
                    )

                cur.execute(
                    """
                    INSERT INTO organizations(id,name)
                    VALUES(%s,%s)
                    """,
                    (organization_id, args.organization_name),
                )
                cur.execute(
                    "SELECT set_config('app.organization_id', %s, true)",
                    (organization_id,),
                )
                cur.execute(
                    """
                    INSERT INTO users(
                        id,email,password_hash,email_verified_at,
                        mfa_enabled,mfa_secret_enc,mfa_enabled_at
                    )
                    VALUES(
                        %s,%s,%s,now(),
                        true,%s,now()
                    )
                    """,
                    (user_id, email, hash_password(password), encrypted_secret),
                )
                cur.execute(
                    """
                    INSERT INTO memberships(organization_id,user_id,role)
                    VALUES(%s,%s,%s)
                    """,
                    (organization_id, user_id, args.role),
                )

    print("E2E provisioning: PASS")
    print("Copy these values into GitHub Actions repository secrets.")
    print(f"E2E_EMAIL={email}")
    print(f"E2E_PASSWORD={password}")
    print(f"E2E_ORGANIZATION_ID={organization_id}")
    print(f"E2E_MFA_SECRET={totp_secret}")
    print(f"STAGING_BASE_URL={os.getenv('STAGING_BASE_URL', '')}")
    print("")
    print("MFA enrollment URI (use once with an authenticator app):")
    print(uri)
    print("")
    print("The TOTP secret is stored encrypted in PostgreSQL.")
    print("Do not commit, log, or share this output.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
