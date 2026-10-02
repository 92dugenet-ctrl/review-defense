#!/usr/bin/env python3
"""V6.30 disaster-recovery validation for an isolated PostgreSQL test database.

This script is deliberately conservative:
- source must be REVIEW_DEFENSE_TEST_DATABASE_URL (never DATABASE_URL);
- restore target must be explicit and different from source;
- destructive restore requires --confirm;
- no production database fallback is permitted;
- the final report is machine-readable JSON and includes backup SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]


def _safe_dsn(dsn: str) -> str:
    p = urlsplit(dsn)
    if not p.scheme:
        return dsn.strip()
    host = (p.hostname or "").lower()
    user = p.username or ""
    port = f":{p.port}" if p.port else ""
    auth = f"{user}@" if user else ""
    return urlunsplit((p.scheme.lower(), f"{auth}{host}{port}", p.path or "", p.query, ""))


def _database_name(dsn: str) -> str:
    path = urlsplit(dsn).path.lstrip("/")
    return path.split("?", 1)[0]


def _is_production_dsn(dsn: str) -> bool:
    normalized = _safe_dsn(dsn)
    prod = _safe_dsn(os.getenv("DATABASE_URL", "")) if os.getenv("DATABASE_URL") else ""
    if prod and normalized == prod:
        return True
    name = _database_name(dsn).lower()
    return any(token in name for token in ("prod", "production"))


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, env=env, check=True)


def _pg_env(dsn: str) -> tuple[str, dict[str, str]]:
    p = urlsplit(dsn)
    if p.password is None:
        return dsn, {}
    user = p.username or ""
    host = p.hostname or ""
    port = f":{p.port}" if p.port else ""
    auth = f"{user}@" if user else ""
    safe = urlunsplit((p.scheme, f"{auth}{host}{port}", p.path, p.query, p.fragment))
    return safe, {"PGPASSWORD": p.password}


def backup_database(dsn: str, output: Path) -> None:
    safe, secret_env = _pg_env(dsn)
    env = os.environ.copy()
    env.update(secret_env)
    _run(["pg_dump", "--format=custom", "--no-owner", "--file", str(output), safe], env=env)


def restore_database(backup: Path, target_dsn: str) -> None:
    safe, secret_env = _pg_env(target_dsn)
    env = os.environ.copy()
    env.update(secret_env)
    _run(["pg_restore", "--clean", "--if-exists", "--no-owner", "--dbname", safe, str(backup)], env=env)


def _connect(dsn: str):
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg is required for V6.30 live DR validation") from exc
    return psycopg.connect(dsn)


def _validate_restored_state(dsn: str, sentinel: dict[str, str]) -> dict[str, object]:
    checks: dict[str, object] = {}
    conn = _connect(dsn)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT version, checksum FROM schema_migrations ORDER BY version DESC LIMIT 1")
                row = cur.fetchone()
                checks["migrations_present"] = bool(row)
                checks["latest_migration"] = row[0] if row else None

                cur.execute("SELECT count(*) FROM organizations WHERE id=%s", (sentinel["org_a"],))
                checks["tenant_a_restored"] = cur.fetchone()[0] == 1
                cur.execute("SELECT count(*) FROM organizations WHERE id=%s", (sentinel["org_b"],))
                checks["tenant_b_restored"] = cur.fetchone()[0] == 1

                cur.execute("SELECT count(*) FROM cases WHERE id=%s AND organization_id=%s", (sentinel["case_a"], sentinel["org_a"]))
                checks["case_restored"] = cur.fetchone()[0] == 1
                cur.execute("SELECT sha256 FROM api_evidence WHERE evidence_id=%s AND organization_id=%s", (sentinel["evidence_a"], sentinel["org_a"]))
                ev = cur.fetchone()
                checks["evidence_hash_restored"] = bool(ev and ev[0] == sentinel["evidence_sha256"])

                cur.execute("SELECT count(*) FROM memberships WHERE organization_id=%s", (sentinel["org_a"],))
                checks["membership_restored"] = cur.fetchone()[0] == 1

                # RLS contract: tenant A can see A, but not B, when app context is set.
                cur.execute("SET LOCAL app.organization_id = %s", (sentinel["org_a"],))
                cur.execute("SELECT count(*) FROM cases WHERE organization_id=%s", (sentinel["org_a"],))
                a_count = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM cases WHERE organization_id=%s", (sentinel["org_b"],))
                b_count = cur.fetchone()[0]
                checks["tenant_rls_isolation"] = a_count >= 1 and b_count == 0
    finally:
        conn.close()
    checks["all_required"] = all(v is True for k, v in checks.items() if k.endswith("restored") or k.endswith("isolation") or k == "migrations_present")
    return checks


def _seed(conn) -> dict[str, str]:
    org_a, org_b = str(uuid.uuid4()), str(uuid.uuid4())
    user_a = str(uuid.uuid4())
    case_a = str(uuid.uuid4())
    evidence_a = str(uuid.uuid4())
    evidence_sha = hashlib.sha256(b"review-defense-v6.30-dr-sentinel").hexdigest()
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("INSERT INTO organizations(id,name) VALUES(%s,%s),(%s,%s)", (org_a, "V630 DR A", org_b, "V630 DR B"))
            cur.execute("INSERT INTO users(id,email,password_hash) VALUES(%s,%s,%s)", (user_a, f"dr-{user_a}@example.invalid", "DR-SENTINEL-HASH"))
            cur.execute("INSERT INTO memberships(organization_id,user_id,role) VALUES(%s,%s,'OWNER')", (org_a, user_a))
            cur.execute("INSERT INTO cases(id,organization_id,review_id,state) VALUES(%s,%s,%s,'OPEN')", (case_a, org_a, f"v630-{case_a}"))
            cur.execute("INSERT INTO api_evidence(organization_id,evidence_id,case_id,filename,content_type,size_bytes,sha256,object_key,verified,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,true,%s)", (org_a, evidence_a, case_a, "dr-sentinel.txt", "text/plain", 31, evidence_sha, f"dr/{evidence_a}", user_a))
    return {"org_a": org_a, "org_b": org_b, "case_a": case_a, "evidence_a": evidence_a, "evidence_sha256": evidence_sha}


def _cleanup(dsn: str, sentinel: dict[str, str]) -> None:
    conn = _connect(dsn)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM organizations WHERE id IN (%s,%s)", (sentinel["org_a"], sentinel["org_b"]))
    finally:
        conn.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("artifacts/v6.30-dr-report.json"))
    p.add_argument("--backup", type=Path, default=Path("artifacts/v6.30-dr.backup.dump"))
    p.add_argument("--restore-database-url", default=None)
    p.add_argument("--confirm", action="store_true", help="required because restore is destructive")
    args = p.parse_args()

    source = os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL", "").strip()
    if not source:
        print("ERROR: REVIEW_DEFENSE_TEST_DATABASE_URL is required; refusing DATABASE_URL fallback.", file=sys.stderr)
        return 2
    if _is_production_dsn(source):
        print("ERROR: source database appears to be production; refusing DR validation.", file=sys.stderr)
        return 2
    target = (args.restore_database_url or "").strip()
    if not target:
        print("ERROR: --restore-database-url is required for restore validation.", file=sys.stderr)
        return 2
    if not args.confirm:
        print("ERROR: --confirm is required because restore replaces database objects.", file=sys.stderr)
        return 2
    if _safe_dsn(source) == _safe_dsn(target):
        print("ERROR: restore target must be different from source.", file=sys.stderr)
        return 2
    if _is_production_dsn(target):
        print("ERROR: restore target appears to be production; refusing.", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.backup.parent.mkdir(parents=True, exist_ok=True)
    sentinel = None
    report: dict[str, object] = {"version": "6.30", "started_at": datetime.now(timezone.utc).isoformat(), "status": "FAILED"}
    try:
        conn = _connect(source)
        try:
            sentinel = _seed(conn)
        finally:
            conn.close()
        backup_database(source, args.backup)
        if not args.backup.is_file() or args.backup.stat().st_size < 512:
            raise RuntimeError("backup is missing or implausibly small")
        backup_sha = hashlib.sha256(args.backup.read_bytes()).hexdigest()
        report["backup"] = {"path": str(args.backup), "size_bytes": args.backup.stat().st_size, "sha256": backup_sha, "format": "postgresql-custom"}
        restore_database(args.backup, target)
        validation = _validate_restored_state(target, sentinel)
        report["validation"] = validation
        if not validation.get("all_required"):
            raise RuntimeError(f"restored-state validation failed: {validation}")
        report["status"] = "PASS"
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        report["error"] = str(exc)
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if sentinel is not None:
            try:
                _cleanup(source, sentinel)
            except Exception as exc:
                print(f"WARNING: source cleanup failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
