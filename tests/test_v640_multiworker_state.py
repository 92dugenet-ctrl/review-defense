from __future__ import annotations

import uuid

import pytest

from src.postgres_api_repository import PostgresAPIRepository


def test_two_repository_instances_share_persisted_case_state():
    """A second API worker must observe state written by the first worker."""
    dsn = __import__("os").getenv("REVIEW_DEFENSE_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("PostgreSQL integration database not configured")

    repo_a = PostgresAPIRepository(dsn)
    repo_b = PostgresAPIRepository(dsn)
    org = str(uuid.uuid4())
    case_id = str(uuid.uuid4())

    # Use the same migration/integration setup as the existing PostgreSQL CI
    # job; this test intentionally models two independent repository instances.
    from src.postgres_integration import IntegrationConfig, connect
    from src.migration_runner import apply_migrations
    from pathlib import Path

    cfg = IntegrationConfig.from_env()
    apply_migrations(lambda: connect(cfg), Path(__file__).resolve().parents[1] / "migrations")
    conn = connect(cfg)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("INSERT INTO organizations(id,name) VALUES(%s,%s)", (org, "P0 multiworker"))
    finally:
        conn.close()

    try:
        repo_a.create_case_persistent(org, case_id, "review-p0", "NEW")
        first = repo_b.get_case_persistent(org, case_id)
        assert first is not None
        assert str(first[0]) == case_id

        repo_a.update_case(org, case_id, status="HUMAN_REVIEW", snapshot_sha256="p0-sha")
        second = repo_b.get_case_persistent(org, case_id)
        assert second[3] == "HUMAN_REVIEW"
        assert second[5] == "p0-sha"

        evidence_id = str(uuid.uuid4())
        repo_a.put_evidence(org, {
            "evidence_id": evidence_id,
            "case_id": case_id,
            "filename": "p0.txt",
            "content_type": "text/plain",
            "size_bytes": 3,
            "sha256": "abc123",
            "object_key": "p0.txt",
            "verified": False,
            "created_by": None,
        })
        before = repo_b.get_evidence(org, evidence_id)
        assert before is not None and before[8] is False
        repo_a.update_evidence_verification(org, evidence_id, str(uuid.uuid4()), "2026-09-25T13:00:00+00:00")
        after = repo_b.get_evidence(org, evidence_id)
        assert after is not None and after[8] is True
    finally:
        conn = connect(cfg)
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM organizations WHERE id=%s", (org,))
        finally:
            conn.close()
