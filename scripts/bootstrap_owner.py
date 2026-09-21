"""V6.37 one-time production OWNER bootstrap.

This is deliberately a deployment/bootstrap operation, not a public signup
route. It creates one organization, one user, and an OWNER membership in a
single PostgreSQL transaction. The plaintext password is never logged.
"""
from __future__ import annotations

import os
from typing import Callable

from src.identity import normalize_email
from src.security_hardening import hash_password


class BootstrapError(RuntimeError):
    pass


def bootstrap_owner(
    dsn: str,
    organization_name: str,
    email: str,
    password: str,
    *,
    confirmation: str,
    connect_factory: Callable[[str], object] | None = None,
) -> tuple[str, str]:
    if confirmation != "CREATE_OWNER":
        raise BootstrapError("BOOTSTRAP_CONFIRM must equal CREATE_OWNER")
    if not dsn:
        raise BootstrapError("DATABASE_URL is required")

    organization_name = organization_name.strip()
    if not organization_name or len(organization_name) > 200:
        raise BootstrapError("organization name is invalid")

    email = normalize_email(email)
    password_hash = hash_password(password)

    if connect_factory is None:
        try:
            import psycopg
        except ImportError as exc:
            raise BootstrapError("psycopg is required") from exc
        connect_factory = psycopg.connect

    conn = connect_factory(dsn)
    try:
        with conn.transaction():
            existing = conn.execute(
                "SELECT EXISTS (SELECT 1 FROM memberships)"
            ).fetchone()[0]
            if existing:
                raise BootstrapError(
                    "bootstrap refused: memberships already exist"
                )

            org_id = conn.execute(
                "INSERT INTO organizations (name) VALUES (%s) RETURNING id",
                (organization_name,),
            ).fetchone()[0]

            user_id = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, password_hash),
            ).fetchone()[0]

            conn.execute(
                """
                INSERT INTO memberships (organization_id, user_id, role)
                VALUES (%s, %s, 'OWNER')
                """,
                (org_id, user_id),
            )

            conn.execute(
                """
                INSERT INTO security_events
                    (organization_id, actor_user_id, event_type,
                     target_user_id, metadata)
                VALUES (%s, %s, 'OWNER_BOOTSTRAPPED', %s, '{}'::jsonb)
                """,
                (org_id, user_id, user_id),
            )

        return str(org_id), str(user_id)
    finally:
        conn.close()


def main() -> int:
    org_id, user_id = bootstrap_owner(
        os.environ.get("DATABASE_URL", ""),
        os.environ.get("BOOTSTRAP_ORG_NAME", ""),
        os.environ.get("BOOTSTRAP_OWNER_EMAIL", ""),
        os.environ.get("BOOTSTRAP_OWNER_PASSWORD", ""),
        confirmation=os.environ.get("BOOTSTRAP_CONFIRM", ""),
    )
    print(
        "owner_bootstrap_complete "
        f"organization_id={org_id} user_id={user_id}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())