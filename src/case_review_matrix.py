"""V6.19 read-only claim/evidence matrix and disposition history helpers."""
from __future__ import annotations
from typing import Any, Iterable

def build_evidence_matrix(*, claims: Iterable[Any], evidence: Iterable[dict[str, Any]], contradictions: Iterable[dict[str, Any]], dispositions: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    dispositions = dispositions or {}
    ev_by_id = {str(e.get("evidence_id")): e for e in evidence}
    ctr_by_claim: dict[str, list[dict[str, Any]]] = {}
    for c in contradictions:
        ctr_by_claim.setdefault(str(c.get("claim_id")), []).append(c)
    rows = []
    for claim in claims:
        if hasattr(claim, "claim_id"):
            claim_id = str(claim.claim_id); text = str(getattr(claim, "text", ""))
        else:
            claim_id = str(claim.get("claim_id")); text = str(claim.get("text", ""))
        linked: list[dict[str, Any]] = []
        for ctr in ctr_by_claim.get(claim_id, []):
            for eid in ctr.get("evidence_ids", []):
                e = ev_by_id.get(str(eid), {"evidence_id": str(eid)})
                linked.append({"evidence_id": str(eid), "sha256": e.get("sha256"), "verified": bool(e.get("verified", True)), "source": e.get("source"), "contradiction_id": ctr.get("contradiction_id"), "disposition": dispositions.get((ctr.get("contradiction_id"),), dispositions.get(ctr.get("contradiction_id")))})
        status = "NO_EVIDENCE" if not linked else ("CONTRADICTION" if ctr_by_claim.get(claim_id) else "SUPPORTED")
        rows.append({"claim_id": claim_id, "claim_text": text, "status": status, "evidence": linked, "requires_human_review": True})
    return rows
