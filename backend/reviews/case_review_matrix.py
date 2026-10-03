"""V6.19 read-only claim/evidence matrix and disposition history helpers."""

from __future__ import annotations

from typing import Any, Iterable


def build_evidence_matrix(
    *,
    claims: Iterable[Any],
    evidence: Iterable[dict[str, Any]],
    contradictions: Iterable[dict[str, Any]],
    dispositions: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    dispositions = dispositions or {}
    evidence_by_id = {
        str(item.get("evidence_id")): item
        for item in evidence
    }
    contradictions_by_claim: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for contradiction in contradictions:
        claim_id = str(contradiction.get("claim_id"))
        contradictions_by_claim.setdefault(
            claim_id,
            [],
        ).append(contradiction)

    rows = []

    for claim in claims:
        if hasattr(claim, "claim_id"):
            claim_id = str(claim.claim_id)
            claim_text = str(
                getattr(claim, "text", "")
            )
        else:
            claim_id = str(claim.get("claim_id"))
            claim_text = str(claim.get("text", ""))

        linked_evidence: list[dict[str, Any]] = []

        for contradiction in contradictions_by_claim.get(
            claim_id,
            [],
        ):
            for evidence_id in contradiction.get(
                "evidence_ids",
                [],
            ):
                evidence_item = evidence_by_id.get(
                    str(evidence_id),
                    {"evidence_id": str(evidence_id)},
                )
                contradiction_id = contradiction.get(
                    "contradiction_id"
                )
                disposition = dispositions.get(
                    (contradiction_id,),
                    dispositions.get(contradiction_id),
                )

                linked_evidence.append(
                    {
                        "evidence_id": str(evidence_id),
                        "sha256": evidence_item.get("sha256"),
                        "verified": bool(
                            evidence_item.get("verified", True)
                        ),
                        "source": evidence_item.get("source"),
                        "contradiction_id": contradiction_id,
                        "disposition": disposition,
                    }
                )

        has_linked_evidence = bool(linked_evidence)
        has_contradictions = bool(
            contradictions_by_claim.get(claim_id)
        )

        if not has_linked_evidence:
            status = "NO_EVIDENCE"
        elif has_contradictions:
            status = "CONTRADICTION"
        else:
            status = "SUPPORTED"

        rows.append(
            {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "status": status,
                "evidence": linked_evidence,
                "requires_human_review": True,
            }
        )

    return rows
