"""V6.5 Structured Contradiction Engine.

Deterministic, human-gated comparison of explicit claim facts against explicit
verified evidence facts. It never infers facts from binary evidence content and
never performs an external/Google action.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
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

_AMOUNT = re.compile(r"(?P<num>\d+(?:[\.,]\d{1,2})?)\s*(?P<currency>€|euros?|eur|\$|usd|dollars?)", re.I)
_DURATION = re.compile(r"(?P<num>\d+(?:[\.,]\d+)?)\s*(?P<unit>h|heures?|hours?|min|minutes?)", re.I)
_DATE = re.compile(r"\b(?:le\s+)?(?P<day>\d{1,2})[/-](?P<month>\d{1,2})(?:[/-](?P<year>\d{2,4}))?\b", re.I)

def _norm_number(value: str) -> str:
    return value.replace(',', '.').rstrip('0').rstrip('.') if '.' in value.replace(',', '.') else value.lstrip('0') or '0'

def extract_claim_facts(claim: ReviewClaim) -> tuple[ClaimFact, ...]:
    out: list[ClaimFact] = []
    for m in _AMOUNT.finditer(claim.text):
        cur = m.group('currency').lower().replace('euros', 'eur').replace('euro', 'eur').replace('dollars', 'usd').replace('$', 'usd').replace('€', 'eur')
        out.append(ClaimFact(claim.claim_id, f"amount:{cur}", "AMOUNT", _norm_number(m.group('num')), claim.text))
    for m in _DURATION.finditer(claim.text):
        unit = m.group('unit').lower()
        canonical = 'HOURS' if unit.startswith(('h', 'heure', 'hour')) else 'MINUTES'
        number = float(m.group('num').replace(',', '.'))
        minutes = number * 60 if canonical == 'HOURS' else number
        out.append(ClaimFact(claim.claim_id, "duration:minutes", "DURATION", _norm_number(str(minutes)), claim.text))
    for m in _DATE.finditer(claim.text):
        year = m.group('year') or ''
        if len(year) == 2: year = '20' + year
        value = f"{int(m.group('day')):02d}-{int(m.group('month')):02d}" + (f"-{year}" if year else '')
        out.append(ClaimFact(claim.claim_id, "date:day", "DATE", value, claim.text))
    return tuple(out)

def contradiction_id(organization_id: str, case_id: str, claim_id: str, key: str, evidence_ids: Iterable[str]) -> str:
    material = "|".join([organization_id, case_id, claim_id, key, *sorted(evidence_ids)])
    return "ctr_" + sha256(material.encode()).hexdigest()[:24]

def detect_contradictions(*, organization_id: str, case_id: str, claims: Iterable[ReviewClaim], evidence_facts: Iterable[EvidenceFact]) -> tuple[ContradictionResult, ...]:
    verified = [f for f in evidence_facts if f.verified]
    by_key: dict[tuple[str, str], list[EvidenceFact]] = {}
    for fact in verified:
        by_key.setdefault((fact.key, fact.kind), []).append(fact)
    results: list[ContradictionResult] = []
    for claim in claims:
        for cf in extract_claim_facts(claim):
            matches = by_key.get((cf.key, cf.kind), [])
            conflicting = [f for f in matches if f.value != cf.value]
            if not conflicting:
                continue
            eids = tuple(sorted({f.evidence_id for f in conflicting}))
            vals = tuple(sorted({f.value for f in conflicting}))
            desc = f"Claim states {cf.kind.lower()} {cf.value!r} for {cf.key}; verified evidence states {', '.join(repr(v) for v in vals)}."
            results.append(ContradictionResult(contradiction_id(organization_id, case_id, claim.claim_id, cf.key, eids), claim.claim_id, eids, cf.key, cf.kind, cf.value, vals, desc, 0.99, True))
    return tuple(results)
