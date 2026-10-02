"""V4.4 Review Intelligence Workspace.

Framework-neutral application-layer contracts for a review-centric workspace.
The workspace is read/analyze oriented: it never submits to Google and never
turns an AI suggestion into a final policy decision.
"""
from dataclasses import dataclass
from typing import Literal
import re

ClaimType = Literal[
    "FACTUAL", "OPINION", "EXPERIENCE", "ALLEGATION", "THREAT",
    "PERSONAL_INFORMATION", "ADVERTISING", "UNKNOWN"
]
ClaimStatus = Literal[
    "UNVERIFIED", "PARTIALLY_SUPPORTED", "SUPPORTED", "CONTRADICTED",
    "NOT_VERIFIABLE"
]
SignalStatus = Literal["POSSIBLE", "RELEVANT", "STRONG", "COUNTER_SIGNAL"]


@dataclass(frozen=True)
class ReviewContext:
    review_id: str
    organization_id: str
    location_id: str
    author_display_name: str | None
    rating: int
    text: str
    published_at: str
    updated_at: str | None = None
    language: str | None = None
    source: str = "GOOGLE"
    review_url: str | None = None


@dataclass(frozen=True)
class ReviewChange:
    change_id: str
    review_id: str
    changed_at: str
    field: str
    before: str | None
    after: str | None
    source: str


@dataclass(frozen=True)
class ReviewHistory:
    review_id: str
    first_seen_at: str
    last_seen_at: str
    changes: tuple[ReviewChange, ...] = ()


@dataclass(frozen=True)
class ReviewClaim:
    claim_id: str
    text: str
    claim_type: ClaimType
    status: ClaimStatus = "UNVERIFIED"
    confidence: float | None = None


@dataclass(frozen=True)
class ReviewPolicySignal:
    code: str
    status: SignalStatus
    justification: str
    claim_ids: tuple[str, ...] = ()
    evidence_required: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewIntelligenceWorkspace:
    review: ReviewContext
    history: ReviewHistory
    claims: tuple[ReviewClaim, ...] = ()
    policy_signals: tuple[ReviewPolicySignal, ...] = ()
    case_id: str | None = None
    human_review_required: bool = False


def _claim_type(text: str) -> ClaimType:
    t = text.strip()
    low = t.lower()
    if not t:
        return "UNKNOWN"
    if re.search(r"\b(paye[zs]?|argent|500 ?€|supprime(?:r)? mes avis|retire(?:r)? (?:cet|mes) avis)\b", low):
        return "THREAT"
    if re.search(r"\b(?:email|e-mail|t[eé]l[eé]phone|num[eé]ro|habite|adresse|06\s?\d{2})\b", low):
        return "PERSONAL_INFORMATION"
    if re.search(r"https?://|www\.|\b(?:appelez|contactez)-?nous\b|\bpromo(?:tion)?\b|\b-\s?\d+%", low):
        return "ADVERTISING"
    if re.search(r"\b(?:m'a vol[eé]|m'ont vol[eé]|arnaque|escroquerie|fraude|a vol[eé])\b", low):
        return "ALLEGATION"
    if re.search(r"\b(?:j'ai|j\s*ai|nous avons|je suis venu|j[eé]tais|on a attendu|j'attends)\b", low):
        return "EXPERIENCE"
    if re.search(r"\b(?:horrible|inadmissible|excellent|nul|cher|lent|mauvais|super)\b", low):
        return "OPINION"
    if re.search(r"\b(?:[0-9]+\s*(?:h|heures?|min|minutes)|[0-9]+\s*€|le\s+\d{1,2}/\d{1,2})\b", low):
        return "FACTUAL"
    return "UNKNOWN"


def extract_claims(review: ReviewContext) -> tuple[ReviewClaim, ...]:
    """Deterministic V4.4 baseline; production AI may enrich, never finalize."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+|\s*;\s*|,\s+(?=(?:c[’']est|c[’']était|mais|cependant)\b)", review.text) if p.strip()]
    claims = []
    for i, part in enumerate(parts, 1):
        ctype = _claim_type(part)
        claims.append(ReviewClaim(f"{review.review_id}-cl{i}", part, ctype))
    return tuple(claims)


def classify_policy_signals(claims: tuple[ReviewClaim, ...]) -> tuple[ReviewPolicySignal, ...]:
    """Map observable text patterns to candidate policy signals only."""
    signals: list[ReviewPolicySignal] = []
    for claim in claims:
        low = claim.text.lower()
        if claim.claim_type == "THREAT":
            signals.append(ReviewPolicySignal(
                "RD-P10", "POSSIBLE", "Potential review-linked demand; verify the demand, benefit and linkage.",
                (claim.claim_id,), ("MESSAGE_OR_SCREENSHOT", "PAYMENT_OR_BENEFIT_REQUEST")))
        elif claim.claim_type == "PERSONAL_INFORMATION":
            signals.append(ReviewPolicySignal(
                "RD-P08", "POSSIBLE", "Potential personal information in review; verify whether the information is unnecessary and identifying.",
                (claim.claim_id,), ("REVIEW_SCREENSHOT",)))
        elif claim.claim_type == "ADVERTISING":
            signals.append(ReviewPolicySignal(
                "RD-P06", "POSSIBLE", "Potential promotional or solicitation content; verify the commercial nature and context.",
                (claim.claim_id,), ("REVIEW_SCREENSHOT",)))
        elif claim.claim_type == "ALLEGATION":
            signals.append(ReviewPolicySignal(
                "RD-P04", "POSSIBLE", "Material allegation detected; verify the underlying facts rather than treating the allegation as established.",
                (claim.claim_id,), ("RECEIPT_OR_RECORD", "TIMELINE")))
        if "concurrent" in low or "copié" in low or "copied" in low:
            signals.append(ReviewPolicySignal(
                "RD-P07", "POSSIBLE", "Potential repetitive/copying pattern; verify across reviews.",
                (claim.claim_id,), ("RELATED_REVIEWS",)))
    # Deduplicate by code while preserving all claim references.
    merged: dict[str, ReviewPolicySignal] = {}
    for signal in signals:
        if signal.code not in merged:
            merged[signal.code] = signal
        else:
            old = merged[signal.code]
            merged[signal.code] = ReviewPolicySignal(
                old.code, old.status, old.justification,
                tuple(dict.fromkeys(old.claim_ids + signal.claim_ids)),
                tuple(dict.fromkeys(old.evidence_required + signal.evidence_required)),
            )
    return tuple(merged.values())


def build_review_workspace(
    review: ReviewContext,
    *,
    history: ReviewHistory | None = None,
    case_id: str | None = None,
) -> ReviewIntelligenceWorkspace:
    """Build a tenant-bound intelligence view without performing an external action."""
    claims = extract_claims(review)
    signals = classify_policy_signals(claims)
    human_review = bool(signals) or any(c.claim_type == "ALLEGATION" for c in claims)
    if history is None:
        history = ReviewHistory(review.review_id, review.published_at, review.updated_at or review.published_at)
    if history.review_id != review.review_id:
        raise ValueError("history does not belong to review")
    return ReviewIntelligenceWorkspace(review, history, claims, signals, case_id, human_review)


def review_belongs_to_organization(review: ReviewContext, organization_id: str) -> bool:
    return review.organization_id == organization_id


def can_view_review(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER"}


def can_modify_review_analysis(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST"}


def can_submit_from_review_workspace(role: str) -> bool:
    # V4.4 deliberately exposes no submission capability from the review workspace.
    return False
