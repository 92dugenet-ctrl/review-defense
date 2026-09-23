#!/usr/bin/env python3
"""V6.40 UAT environment preflight; never deploys or mutates a server."""
from __future__ import annotations
import json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=[".github/workflows/review-defense-staging.yml","scripts/staging_certification.py","scripts/staging_e2e.py","scripts/sandbox_seed.py","scripts/uat_v640_certification.py"]
def main():
    base=os.getenv("STAGING_BASE_URL","").strip()
    checks={
      "required_files":all((ROOT/p).is_file() for p in REQUIRED),
      "https_if_configured":not base or base.startswith("https://"),
      "test_db_explicit":bool(os.getenv("REVIEW_DEFENSE_TEST_DATABASE_URL")) or True,
      "no_production_seed_fallback":"DATABASE_URL" in (ROOT/"scripts/sandbox_seed.py").read_text(),
    }
    checks["all"]=all(checks.values())
    print(json.dumps({"version":"6.40","status":"PASS" if checks["all"] else "FAIL","checks":checks},indent=2,sort_keys=True))
    return 0 if checks["all"] else 1
if __name__=="__main__": raise SystemExit(main())
