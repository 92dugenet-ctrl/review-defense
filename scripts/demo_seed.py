#!/usr/bin/env python3
"""Seed one realistic fictitious dossier into the authenticated staging account.

This script ONLY uses the authenticated Review Defense API. It never connects to
PostgreSQL directly and never calls Google or any external review service.

Required environment:
  STAGING_BASE_URL
  E2E_EMAIL
  E2E_PASSWORD
  E2E_ORGANIZATION_ID
  E2E_MFA_SECRET (required when the staging account enforces MFA)

The seed is idempotent: the stable demo review ID and idempotency key prevent
duplicate demo dossiers across repeated runs.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEMO_REVIEW_ID = "RD-DEMO-2026-001"
DEMO_CASE_IDEMPOTENCY_KEY = "review-defense-demo-case-2026-001"


def request_json(
    base: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    idempotency_key: str | None = None,
) -> tuple[int, dict]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    payload = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=payload,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:2000]}
        return exc.code, payload


def login(base: str) -> str:
    email = os.environ["E2E_EMAIL"]
    password = os.environ["E2E_PASSWORD"]
    organization_id = os.environ["E2E_ORGANIZATION_ID"]
    mfa_secret = os.getenv("E2E_MFA_SECRET", "").strip()

    common = {
        "email": email,
        "organization_id": organization_id,
        "password": password,
    }

    if mfa_secret:
        status, payload = request_json(base, "POST", "/v1/auth/login", body=common)
        if status != 401:
            raise RuntimeError(
                f"expected MFA challenge before demo seed, received HTTP {status}"
            )
        from src.mfa import totp_code
        common["mfa_code"] = totp_code(mfa_secret)

    status, payload = request_json(base, "POST", "/v1/auth/login", body=common)
    token = payload.get("access_token")
    if status != 200 or not token:
        raise RuntimeError(f"staging authentication failed: HTTP {status}")
    return str(token)


def seed_demo(base: str, token: str) -> dict:
    review = {
        "review_id": DEMO_REVIEW_ID,
        "location_id": "demo-hotel-bellevue-paris",
        "author_display_name": "Client fictif — Démonstration",
        "rating": 1,
        "text": (
            "Séjour très décevant. La chambre n'était pas propre à notre arrivée "
            "et personne n'a réellement pris le problème au sérieux."
        ),
        "published_at": "2026-09-20T10:00:00Z",
        "updated_at": "2026-09-20T10:00:00Z",
        "language": "fr",
        "review_url": "https://example.invalid/review/RD-DEMO-2026-001",
    }

    status, payload = request_json(
        base, "POST", "/v1/reviews", token=token, body=review
    )
    if status not in (201,):
        raise RuntimeError(f"demo review creation failed: HTTP {status} {payload}")

    status, reviews = request_json(base, "GET", "/v1/reviews", token=token)
    if status != 200:
        raise RuntimeError(f"demo review verification failed: HTTP {status} {reviews}")

    status, cases = request_json(base, "GET", "/v1/cases", token=token)
    if status != 200:
        raise RuntimeError(f"demo case lookup failed: HTTP {status} {cases}")

    existing = next(
        (item for item in cases.get("items", []) if item.get("review_id") == DEMO_REVIEW_ID),
        None,
    )
    if existing:
        case = existing
        case_created = False
    else:
        status, created = request_json(
            base,
            "POST",
            "/v1/cases",
            token=token,
            idempotency_key=DEMO_CASE_IDEMPOTENCY_KEY,
            body={"review_id": DEMO_REVIEW_ID},
        )
        if status not in (201,):
            raise RuntimeError(f"demo case creation failed: HTTP {status} {created}")
        case = created.get("case", created)
        case_created = True

    return {
        "status": "PASS",
        "demo": {
            "review_id": DEMO_REVIEW_ID,
            "case_id": case.get("case_id"),
            "case_status": case.get("status"),
            "case_created_now": case_created,
            "external_action": False,
            "fictitious_data": True,
        },
    }


def main() -> int:
    required = [
        "STAGING_BASE_URL",
        "E2E_EMAIL",
        "E2E_PASSWORD",
        "E2E_ORGANIZATION_ID",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("demo seed: FAIL: missing " + ", ".join(missing), file=sys.stderr)
        return 1

    base = os.environ["STAGING_BASE_URL"].rstrip("/")
    if not base.startswith("https://"):
        print("demo seed: FAIL: STAGING_BASE_URL must use HTTPS", file=sys.stderr)
        return 1

    try:
        token = login(base)
        result = seed_demo(base, token)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("demo seed: PASS")
        return 0
    except Exception as exc:
        print(f"demo seed: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
