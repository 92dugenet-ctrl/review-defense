"""V6.5 Structured Contradiction Engine.

Deterministic, human-gated comparison of explicit claim facts against explicit
verified evidence facts. It never infers facts from binary evidence content and
never performs an external/Google action.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Iterable

from .review_workspace import ReviewClaim


@dataclass(frozen=True)
class ClaimFact:
    claim_id: str
    key: str
    kind: str
    value: str
    source_text: str


@dataclass(frozen=True)
class EvidenceFact:
    evidence_id: str
    key: str
    kind: str
    value: str
    source_location: str = ""
    verified: bool = False


@dataclass(frozen=True)
class ContradictionResult:
    contradiction_id: str
    claim_id: str
    evidence_ids: tuple[str, ...]
    key: str
    kind: str
    claim_value: str
    evidence_values: tuple[str, ...]
    description: str
    confidence: float
    requires_human_review: bool = True


_AMOUNT = re.compile(
    r"(?P<num>\d+(?:[\.,]\d{1,2})?)\s*"
    r"(?P<currency>€|euros?|eur|\$|usd|dollars?)",
    re.I,
)
_DURATION = re.compile(
    r"(?P<num>\d+(?:[\.,]\d+)?)\s*"
    r"(?P<unit>h|heures?|hours?|min|minutes?)",
    re.I,
)
_DATE = re.compile(
    r"\b(?:le\s+)?(?P<day>\d{1,2})[/-]"
    r"(?P<month>\d{1,2})"
    r"(?:[/-](?P<year>\d{2,4}))?\b",
    re.I,
)


def _norm_number(value: str) -> str:
    normalized_value = value.replace(",", ".")

    if "." in normalized_value:
        return normalized_value.rstrip("0").rstrip(".")

    return normalized_value.lstrip("0") or "0"


def extract_claim_facts(
    claim: ReviewClaim,
) -> tuple[ClaimFact, ...]:
    facts: list[ClaimFact] = []

    for match in _AMOUNT.finditer(claim.text):
        currency = (
            match.group("currency")
            .lower()
            .replace("euros", "eur")
            .replace("euro", "eur")
            .replace("dollars", "usd")
            .replace("$", "usd")
            .replace("€", "eur")
        )
        facts.append(
            ClaimFact(
                claim.claim_id,
                f"amount:{currency}",
                "AMOUNT",
                _norm_number(match.group("num")),
                claim.text,
            )
        )

    for match in _DURATION.finditer(claim.text):
        unit = match.group("unit").lower()
        canonical_unit = (
            "HOURS"
            if unit.startswith(("h", "heure", "hour"))
            else "MINUTES"
        )
        number = float(match.group("num").replace(",", "."))
        minutes = (
            number * 60
            if canonical_unit == "HOURS"
            else number
        )
        facts.append(
            ClaimFact(
                claim.claim_id,
                "duration:minutes",
                "DURATION",
                _norm_number(str(minutes)),
                claim.text,
            )
        )

    for match in _DATE.finditer(claim.text):
        year = match.group("year") or ""

        if len(year) == 2:
            year = "20" + year

        value = (
            f"{int(match.group('day')):02d}-"
            f"{int(match.group('month')):02d}"
        )

        if year:
            value += f"-{year}"

        facts.append(
            ClaimFact(
                claim.claim_id,
                "date:day",
                "DATE",
                value,
                claim.text,
            )
        )

    return tuple(facts)


def contradiction_id(
    organization_id: str,
    case_id: str,
    claim_id: str,
    key: str,
    evidence_ids: Iterable[str],
) -> str:
    material_parts = [
        organization_id,
        case_id,
        claim_id,
        key,
        *sorted(evidence_ids),
    ]
    material = "|".join(material_parts)
    digest = sha256(material.encode()).hexdigest()[:24]

    return "ctr_" + digest


def detect_contradictions(
    *,
    organization_id: str,
    case_id: str,
    claims: Iterable[ReviewClaim],
    evidence_facts: Iterable[EvidenceFact],
) -> tuple[ContradictionResult, ...]:
    verified_facts = [
        fact
        for fact in evidence_facts
        if fact.verified
    ]
    evidence_by_key: dict[
        tuple[str, str],
        list[EvidenceFact],
    ] = {}

    for fact in verified_facts:
        key = (fact.key, fact.kind)
        evidence_by_key.setdefault(key, []).append(fact)

    results: list[ContradictionResult] = []

    for claim in claims:
        claim_facts = extract_claim_facts(claim)

        for claim_fact in claim_facts:
            key = (claim_fact.key, claim_fact.kind)
            matching_facts = evidence_by_key.get(key, [])
            conflicting_facts = [
                fact
                for fact in matching_facts
                if fact.value != claim_fact.value
            ]

            if not conflicting_facts:
                continue

            evidence_ids = tuple(
                sorted(
                    {
                        fact.evidence_id
                        for fact in conflicting_facts
                    }
                )
            )
            evidence_values = tuple(
                sorted(
                    {
                        fact.value
                        for fact in conflicting_facts
                    }
                )
            )
            description = (
                f"Claim states {claim_fact.kind.lower()} "
                f"{claim_fact.value!r} for {claim_fact.key}; "
                "verified evidence states "
                f"{', '.join(repr(value) for value in evidence_values)}."
            )

            results.append(
                ContradictionResult(
                    contradiction_id(
                        organization_id,
                        case_id,
                        claim.claim_id,
                        claim_fact.key,
                        evidence_ids,
                    ),
                    claim.claim_id,
                    evidence_ids,
                    claim_fact.key,
                    claim_fact.kind,
                    claim_fact.value,
                    evidence_values,
                    description,
                    0.99,
                    True,
                )
            )

    return tuple(results)
