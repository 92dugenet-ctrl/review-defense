#!/usr/bin/env python3
"""V6.40 isolated demonstration sandbox seed.

This script only targets REVIEW_DEFENSE_TEST_DATABASE_URL. It refuses DATABASE_URL,
never calls Google or any external service, and seeds two independent tenants with
users, reviews, cases, evidence, decisions, approvals, submissions, alerts and audit
data so the frontend can be exercised against realistic-but-fictitious state.

Usage:
  REVIEW_DEFENSE_TEST_DATABASE_URL=postgresql://... python scripts/sandbox_seed.py

The seed is repeatable: existing organizations whose names start with
"Review Defense Sandbox" are removed first.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.migration_runner import apply_migrations
from src.postgres_integration import IntegrationConfig, connect, wait_for_database


PREFIX = "Review Defense Sandbox"
PASSWORD = "Sandbox-Demo-2026!"


def require_test_database() -> IntegrationConfig:
    dsn = os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL", "").strip()
    if not dsn:
        raise RuntimeError("REVIEW_DEFENSE_TEST_DATABASE_URL is required")
    if os.getenv("DATABASE_URL") and dsn == os.getenv("DATABASE_URL"):
        raise RuntimeError("Refusing to use DATABASE_URL for sandbox data")
    return IntegrationConfig.from_env()


def seed_tenant(cur, org_name: str, slug: str) -> dict[str, str]:
    cur.execute(
        "INSERT INTO organizations(name) VALUES(%s) RETURNING id",
        (org_name,),
    )
    org_id = str(cur.fetchone()[0])
    cur.execute("SET LOCAL app.organization_id = %s", (org_id,))

    users: dict[str, str] = {}
    roles = [
        ("owner", "owner@demo.review-defense.invalid", "OWNER"),
        ("admin", "admin@demo.review-defense.invalid", "ADMIN"),
        ("analyst", "analyst@demo.review-defense.invalid", "ANALYST"),
        ("client", "client@demo.review-defense.invalid", "CLIENT"),
        ("viewer", "viewer@demo.review-defense.invalid", "VIEWER"),
    ]
    for key, email, role in roles:
        cur.execute(
            """
            INSERT INTO users(email, password_hash, email_verified_at, mfa_enabled)
            VALUES(%s, crypt(%s, gen_salt('bf')), now(), %s)
            RETURNING id
            """,
            (f"{slug}.{email}", PASSWORD, role in ("OWNER", "ADMIN")),
        )
        user_id = str(cur.fetchone()[0])
        users[key] = user_id
        cur.execute(
            "INSERT INTO memberships(organization_id,user_id,role) VALUES(%s,%s,%s)",
            (org_id, user_id, role),
        )

    cur.execute(
        """
        INSERT INTO organization_sla_calendars(organization_id,timezone,workdays,start_hour,end_hour)
        VALUES(%s,'Europe/Paris','[0,1,2,3,4,5]'::jsonb,8,18)
        ON CONFLICT (organization_id) DO NOTHING
        """,
        (org_id,),
    )
    cur.execute(
        "INSERT INTO organization_runtime_settings(organization_id,settings) VALUES(%s,%s::jsonb)",
        (org_id, '{"sandbox":true,"version":"6.40","external_actions_enabled":false}'),
    )
    cur.execute(
        "INSERT INTO organization_notification_policies(organization_id) VALUES(%s)",
        (org_id,),
    )

    reviews = [
        ("review-positive", 5, "Accueil excellent et service rapide.", "DEMO"),
        ("review-critical", 1, "Le service était très mauvais et la commande incomplète.", "DEMO"),
        ("review-neutral", 3, "Expérience correcte, quelques points à améliorer.", "DEMO"),
    ]
    for review_id, rating, text, source in reviews:
        cur.execute(
            """
            INSERT INTO api_reviews
              (organization_id,review_id,location_id,author_display_name,rating,review_text,
               published_at,updated_at,language,source,review_url)
            VALUES(%s,%s,'demo-location','Client fictif',%s,%s,
                   '2026-09-15T10:00:00Z','2026-09-15T10:00:00Z','fr',%s,
                   'https://example.invalid/review/' || %s)
            """,
            (org_id, f"{slug}-{review_id}", rating, text, source, review_id),
        )

    case_ids: dict[str, str] = {}
    cases = [
        ("open", "OPEN", f"{slug}-review-critical"),
        ("frozen", "FROZEN", f"{slug}-review-neutral"),
        ("approved", "APPROVED", f"{slug}-review-positive"),
    ]
    for key, status, review_id in cases:
        case_id = str(uuid.uuid4())
        case_ids[key] = case_id
        cur.execute(
            """
            INSERT INTO cases(id,organization_id,review_id,state)
            VALUES(%s,%s,%s,%s)
            """,
            (case_id, org_id, review_id, status),
        )
        cur.execute(
            """
            INSERT INTO api_cases(organization_id,case_id,review_id,status,assigned_to)
            VALUES(%s,%s,%s,%s,%s)
            """,
            (org_id, case_id, review_id, status, users["analyst"]),
        )
        cur.execute(
            """
            INSERT INTO case_events(organization_id,case_id,event_type,actor_user_id,payload)
            VALUES(%s,%s,'SANDBOX_CREATED',%s,%s::jsonb)
            """,
            (org_id, case_id, users["owner"], '{"sandbox":true}'),
        )

    evidence_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO api_evidence
          (organization_id,evidence_id,case_id,filename,content_type,size_bytes,sha256,object_key,
           verified,created_by,verified_by,verified_at)
        VALUES(%s,%s,%s,'demo-order.pdf','application/pdf',18432,
               'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
               %s,true,%s,%s,now())
        """,
        (org_id, evidence_id, case_ids["approved"],
         f"sandbox/{slug}/demo-order.pdf", users["analyst"], users["admin"]),
    )
    cur.execute(
        """
        INSERT INTO evidence_facts
          (organization_id,evidence_id,case_id,key,kind,value,verified,verified_by,verified_at)
        VALUES(%s,%s,%s,'order_status','text','DELIVERED',true,%s,now())
        """,
        (org_id, evidence_id, case_ids["approved"], users["admin"]),
    )

    decision_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO api_decisions
          (organization_id,decision_id,case_id,status,kind,rationale,snapshot_sha256,created_by)
        VALUES(%s,%s,%s,'DECIDED','PREPARE_SUBMISSION',
               'Sandbox decision: human review remains required.',
               'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',%s)
        """,
        (org_id, decision_id, case_ids["approved"], users["analyst"]),
    )
    cur.execute(
        """
        INSERT INTO api_dossier_snapshots
          (organization_id,case_id,sha256,payload,frozen_by)
        VALUES(%s,%s,'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
               %s::jsonb,%s)
        """,
        (org_id, case_ids["approved"],
         '{"sandbox":true,"human_gate":"required","external_action":false}', users["analyst"]),
    )
    approval_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO api_approvals
          (organization_id,approval_id,case_id,decision_id,actor_id,actor_role,snapshot_sha256,approved_at)
        VALUES(%s,%s,%s,%s,%s,'ADMIN',
               'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',now())
        """,
        (org_id, approval_id, case_ids["approved"], decision_id, users["admin"]),
    )
    cur.execute(
        """
        INSERT INTO api_submissions(organization_id,submission_id,case_id,status,external_call)
        VALUES(%s,%s,%s,'PREPARED',false)
        """,
        (org_id, str(uuid.uuid4()), case_ids["approved"] ),
    )

    contradiction_id = f"{slug}-contradiction-1"
    cur.execute(
        """
        INSERT INTO contradiction_findings
          (organization_id,contradiction_id,case_id,claim_id,key,kind,claim_value,
           evidence_ids,evidence_values,description,confidence,requires_human_review)
        VALUES(%s,%s,%s,'claim-1','delivery_status','text','NOT_DELIVERED',
               %s::jsonb,%s::jsonb,'Fictitious contradiction for human-review testing.',0.87,true)
        """,
        (org_id, contradiction_id, case_ids["approved"],
         f'["{evidence_id}"]', '["DELIVERED"]'),
    )
    cur.execute(
        """
        INSERT INTO case_review_checklist(item_id,organization_id,case_id,code,label,required,completed,completed_by,completed_at)
        VALUES(%s,%s,%s,'EVIDENCE_REVIEWED','Review evidence',true,true,%s,now())
        """,
        (str(uuid.uuid4()), org_id, case_ids["approved"], users["analyst"]),
    )
    cur.execute(
        """
        INSERT INTO notification_outbox
          (organization_id,notification_id,case_id,escalation_level,channel,target,subject,body,status,dedupe_key)
        VALUES(%s,%s,%s,'CRITICAL','IN_APP','sandbox',
               'Sandbox alert','Fictitious alert for UI testing','PENDING',%s)
        """,
        (org_id, str(uuid.uuid4()), case_ids["open"], f"{slug}-alert-1"),
    )
    cur.execute(
        """
        INSERT INTO security_events(organization_id,actor_user_id,event_type,metadata)
        VALUES(%s,%s,'SANDBOX_SEED',%s::jsonb)
        """,
        (org_id, users["owner"], '{"sandbox":true,"external_action":false}'),
    )
    return {"organization_id": org_id, **{f"user_{k}": v for k, v in users.items()}}


def main() -> int:
    try:
        cfg = require_test_database()
        wait_for_database(cfg)
        apply_migrations(lambda: connect(cfg), ROOT / "migrations")

        conn = connect(cfg)
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    # Demo organizations are disposable and never overlap production naming.
                    cur.execute(
                        "DELETE FROM organizations WHERE name LIKE %s",
                        (PREFIX + " %",),
                    )
                    cur.execute(
                        "DELETE FROM users WHERE email::text LIKE %s",
                        ("%.%\u0040demo.review-defense.invalid",),
                    )
                    result_a = seed_tenant(cur, f"{PREFIX} Alpha", "alpha")
                    result_b = seed_tenant(cur, f"{PREFIX} Beta", "beta")
        finally:
            conn.close()

        print("sandbox seed: PASS")
        print("sandbox tenants: Alpha, Beta")
        print("sandbox users per tenant: OWNER, ADMIN, ANALYST, CLIENT, VIEWER")
        print("sandbox external actions: DISABLED")
        return 0
    except Exception as exc:
        print(f"sandbox seed: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
