#!/usr/bin/env python3
"""Seed a complete synthetic demonstration dossier into authenticated staging.

This script uses only the authenticated Review Defense API. It never connects
directly to PostgreSQL and never calls Google or any external review service.

The demo is deliberately rich enough to exercise:
review -> claims -> policy signal -> evidence -> verification -> fact extraction
-> contradiction analysis -> readiness -> human decision gates.

All data is explicitly fictitious.
"""
from __future__ import annotations

import base64
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

DEMO_REVIEW_TEXT = (
    "J'ai attendu 45 minutes avant qu'on me réponde. "
    "La chambre n'était pas propre à notre arrivée. "
    "L'hôtel m'a volé 200 € sur la facture."
)

DEMO_EVIDENCE = (
    {
        "filename": "01-facture-sejour-demo.txt",
        "content": (
            "DOCUMENT FICTIF — FACTURE HÔTEL BELLEVUE\n"
            "Date du séjour : 20/09/2026\n"
            "Montant total facturé : 150 €\n"
            "Aucune autre somme facturée sur cette facture de démonstration.\n"
        ),
        "facts": [
            {"key": "amount:eur", "kind": "AMOUNT", "value": "150", "source_location": "ligne 3"},
            {"key": "date:day", "kind": "DATE", "value": "20-09-2026", "source_location": "ligne 2"},
        ],
    },
    {
        "filename": "02-rapport-menage-demo.txt",
        "content": (
            "DOCUMENT FICTIF — RAPPORT DE MÉNAGE\n"
            "Chambre : 204\n"
            "Contrôle après arrivée : conforme\n"
            "Intervention de contrôle : 15 minutes après le signalement\n"
        ),
        "facts": [
            {"key": "duration:minutes", "kind": "DURATION", "value": "15", "source_location": "ligne 4"},
        ],
    },
    {
        "filename": "03-journal-reception-demo.txt",
        "content": (
            "DOCUMENT FICTIF — JOURNAL DE RÉCEPTION\n"
            "15:20 — Signalement du client enregistré.\n"
            "15:35 — Retour vers le client et proposition d'intervention.\n"
            "Traitement : 15 minutes.\n"
        ),
        "facts": [
            {"key": "duration:minutes", "kind": "DURATION", "value": "15", "source_location": "ligne 4"},
        ],
    },
)


def request_json(
    base: str,
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    idempotency_key: str | None = None,
) -> tuple[int, dict]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base.rstrip("/") + path, data=payload, headers=headers, method=method)
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
    common = {"email": email, "organization_id": organization_id, "password": password}
    if mfa_secret:
        status, _ = request_json(base, "POST", "/v1/auth/login", body=common)
        if status != 401:
            raise RuntimeError(f"expected MFA challenge, received HTTP {status}")
        from src.mfa import totp_code
        common["mfa_code"] = totp_code(mfa_secret)
    status, payload = request_json(base, "POST", "/v1/auth/login", body=common)
    token = payload.get("access_token")
    if status != 200 or not token:
        raise RuntimeError(f"staging authentication failed: HTTP {status}")
    return str(token)


def wait_for_live_contract(base: str, token: str, cases: dict) -> None:
    """Wait until the deployed API exposes the source-preservation fix."""
    import time
    existing = next((item for item in cases.get("items", []) if item.get("review_id") == DEMO_REVIEW_ID), None)
    if not existing:
        return
    case_id = str(existing["case_id"])
    last = None
    for _ in range(36):
        status, payload = request_json(base, "GET", f"/v1/cases/{case_id}/workspace", token=token)
        if status == 200:
            source = payload.get("workspace", {}).get("review", {}).get("source")
            if source == "GOOGLE":
                return
            last = f"workspace source={source!r}"
        else:
            last = f"HTTP {status}"
        time.sleep(5)
    raise RuntimeError(f"live deployment did not expose the new workspace contract: {last}")


def ensure_evidence(base: str, token: str, case_id: str) -> list[dict]:
    status, payload = request_json(base, "GET", f"/v1/cases/{case_id}/workspace", token=token)
    if status != 200:
        raise RuntimeError(f"workspace evidence lookup failed: HTTP {status}")
    existing = {}
    for item in payload.get("evidence_tasks", []):
        if item.get("filename"):
            existing[item["filename"]] = item

    result = []
    for spec in DEMO_EVIDENCE:
        row = existing.get(spec["filename"])
        if row is None:
            encoded = base64.b64encode(spec["content"].encode("utf-8")).decode("ascii")
            body = {
                "case_id": case_id,
                "filename": spec["filename"],
                "content_type": "text/plain",
                "content_base64": encoded,
                "facts": spec["facts"],
            }
            status, created = request_json(base, "POST", "/v1/evidence", token=token, body=body)
            if status != 201:
                raise RuntimeError(f"evidence creation failed for {spec['filename']}: HTTP {status} {created}")
            row = created.get("evidence", created)

        eid = str(row["evidence_id"])

        status, verified = request_json(base, "POST", f"/v1/evidence/{eid}/verify", token=token)
        if status not in (200, 409):
            raise RuntimeError(f"evidence verification failed for {eid}: HTTP {status} {verified}")

        status, facts = request_json(base, "POST", f"/v1/evidence/{eid}/facts/verify", token=token, body={})
        if status != 200:
            raise RuntimeError(f"fact verification failed for {eid}: HTTP {status} {facts}")

        result.append({"evidence_id": eid, "filename": spec["filename"]})

    status, extracted = request_json(
        base,
        "POST",
        f"/v1/cases/{case_id}/extract-facts",
        token=token,
        body={"evidence_ids": [x["evidence_id"] for x in result]},
    )
    if status != 200:
        raise RuntimeError(f"fact extraction failed: HTTP {status} {extracted}")

    status, contradictions = request_json(
        base,
        "POST",
        f"/v1/cases/{case_id}/contradictions",
        token=token,
        body={"evidence_ids": [x["evidence_id"] for x in result]},
    )
    if status != 200:
        raise RuntimeError(f"contradiction analysis failed: HTTP {status} {contradictions}")

    return [
        *result,
        {
            "verified": True,
            "fact_suggestions": extracted.get("count", 0),
            "contradictions": contradictions.get("count", 0),
        },
    ]


def seed_demo(base: str, token: str) -> dict:
    review = {
        "review_id": DEMO_REVIEW_ID,
        "location_id": "demo-hotel-bellevue-paris",
        "author_display_name": "Client fictif — Démonstration",
        "rating": 1,
        "text": DEMO_REVIEW_TEXT,
        "published_at": "2026-09-20T10:00:00Z",
        "updated_at": "2026-09-20T10:00:00Z",
        "language": "fr",
        "source": "GOOGLE",
        "review_url": "https://example.invalid/review/RD-DEMO-2026-001",
    }
    status, payload = request_json(base, "POST", "/v1/reviews", token=token, body=review)
    if status != 201:
        raise RuntimeError(f"demo review creation failed: HTTP {status} {payload}")

    status, cases = request_json(base, "GET", "/v1/cases", token=token)
    if status != 200:
        raise RuntimeError(f"demo case lookup failed: HTTP {status} {cases}")
    wait_for_live_contract(base, token, cases)
    status, cases = request_json(base, "GET", "/v1/cases", token=token)
    if status != 200:
        raise RuntimeError(f"demo case lookup failed after deployment wait: HTTP {status} {cases}")
    existing = next((x for x in cases.get("items", []) if x.get("review_id") == DEMO_REVIEW_ID), None)

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
        if status != 201:
            raise RuntimeError(f"demo case creation failed: HTTP {status} {created}")
        case = created.get("case", created)
        case_created = True

    case_id = str(case["case_id"])
    evidence = ensure_evidence(base, token, case_id)

    status, workspace = request_json(base, "GET", f"/v1/cases/{case_id}/workspace", token=token)
    if status != 200:
        raise RuntimeError(f"workspace verification failed: HTTP {status}")

    review_payload = workspace.get("workspace", {}).get("review", {})
    if review_payload.get("source") != "GOOGLE":
        raise RuntimeError("workspace review source is not preserved as GOOGLE")

    return {
        "status": "PASS",
        "demo": {
            "review_id": DEMO_REVIEW_ID,
            "case_id": case_id,
            "case_status": case.get("status"),
            "case_created_now": case_created,
            "evidence_count": len([x for x in evidence if x.get("evidence_id")]),
            "contradictions": evidence[-1].get("contradictions", 0),
            "fact_suggestions": evidence[-1].get("fact_suggestions", 0),
            "external_action": False,
            "fictitious_data": True,
        },
    }


def main() -> int:
    required = ["STAGING_BASE_URL", "E2E_EMAIL", "E2E_PASSWORD", "E2E_ORGANIZATION_ID"]
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
