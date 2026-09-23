#!/usr/bin/env python3
"""Seed the deterministic V6.40 UAT fixture into the disposable test database."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"tests/fixtures/v640_uat_dataset.json"

def main() -> int:
    dsn=os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL","").strip()
    if not dsn:
        print("REVIEW_DEFENSE_TEST_DATABASE_URL is required; refusing to seed", file=sys.stderr)
        return 2
    if os.getenv("DATABASE_URL") and dsn == os.getenv("DATABASE_URL"):
        print("Refusing to seed DATABASE_URL", file=sys.stderr)
        return 2
    data=json.loads(FIXTURE.read_text(encoding="utf-8"))
    if data.get("version")!="6.40" or data.get("external_actions_enabled") is not False:
        print("invalid deterministic fixture", file=sys.stderr)
        return 1
    if [t["key"] for t in data["tenants"]] != ["A","B"]:
        print("fixture tenant order is not deterministic", file=sys.stderr)
        return 1
    env=dict(os.environ)
    env["REVIEW_DEFENSE_TEST_DATABASE_URL"]=dsn
    result=subprocess.run([sys.executable,str(ROOT/"scripts/sandbox_seed.py")],env=env,check=False)
    return result.returncode

if __name__=="__main__":
    raise SystemExit(main())
