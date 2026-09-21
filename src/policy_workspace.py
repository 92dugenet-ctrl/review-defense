"""V4.5 Policy Intelligence Workspace.

Framework-neutral policy registry and review contracts. Policy edits are staged
and require explicit human validation; this module never submits external actions.
"""
from dataclasses import dataclass
from typing import Literal

PolicyStatus = Literal["ACTIVE", "DRAFT", "DEPRECATED"]
SignalKind = Literal["SIGNAL", "COUNTER_SIGNAL"]
ValidationStatus = Literal["PENDING", "VALIDATED", "REJECTED"]

@dataclass(frozen=True)
class PolicySignalDefinition:
    code: str
    kind: SignalKind
    name: str
    description: str
    evidence_required: tuple[str, ...] = ()

@dataclass(frozen=True)
class PolicyDefinition:
    code: str
    name: str
    description: str
    status: PolicyStatus
    version: str
    signals: tuple[PolicySignalDefinition, ...]
    human_review_required: bool = True

@dataclass(frozen=True)
class PolicyVersion:
    code: str
    version: str
    definitions: tuple[PolicySignalDefinition, ...]
    created_at: str
    validation_status: ValidationStatus = "PENDING"
    validated_by: str | None = None

@dataclass(frozen=True)
class PolicyWorkspace:
    organization_id: str
    policies: tuple[PolicyDefinition, ...]
    versions: tuple[PolicyVersion, ...] = ()

POLICIES: tuple[PolicyDefinition, ...] = (
    PolicyDefinition("RD-P01", "Fake engagement", "Potentially fabricated or non-genuine review activity.", "ACTIVE", "1.0", (
        PolicySignalDefinition("NO_REAL_EXPERIENCE", "SIGNAL", "No real experience", "Reviewer indicates no genuine interaction.", ("BOOKING_OR_CUSTOMER_RECORD",)),
        PolicySignalDefinition("PAID_REVIEW", "SIGNAL", "Paid review", "Review appears incentivized or purchased.", ("MESSAGE_OR_PAYMENT_RECORD",)),
        PolicySignalDefinition("MULTIPLE_ACCOUNTS", "SIGNAL", "Multiple accounts", "Potential coordinated use of accounts.", ("RELATED_REVIEW_ACTIVITY",)),
        PolicySignalDefinition("NO_RELEVANT_INTERACTION", "COUNTER_SIGNAL", "Relevant interaction exists", "Evidence shows a genuine customer interaction.", ("RECEIPT_OR_BOOKING",)),
    )),
    PolicyDefinition("RD-P02", "Rating manipulation", "Potential manipulation of ratings or review solicitation patterns.", "ACTIVE", "1.0", (
        PolicySignalDefinition("UNUSUAL_REVIEW_VOLUME", "SIGNAL", "Unusual review volume", "Review activity materially differs from the normal pattern.", ("REVIEW_ACTIVITY_TIMELINE",)),
        PolicySignalDefinition("INCENTIVIZED_REVIEW", "SIGNAL", "Incentivized review", "Review appears connected to an incentive.", ("OFFER_OR_MESSAGE",)),
        PolicySignalDefinition("NORMAL_REVIEW_PATTERN", "COUNTER_SIGNAL", "Normal review pattern", "Activity is consistent with ordinary review behavior.", ("REVIEW_ACTIVITY_TIMELINE",)),
    )),
    PolicyDefinition("RD-P03", "Conflict of interest", "Potential reviewer relationship that creates a conflict of interest.", "ACTIVE", "1.0", (
        PolicySignalDefinition("EMPLOYEE", "SIGNAL", "Employee relationship", "Reviewer may be an employee.", ("EMPLOYMENT_RECORD",)),
        PolicySignalDefinition("FORMER_EMPLOYEE", "SIGNAL", "Former employee", "Reviewer may have a former employment relationship.", ("EMPLOYMENT_RECORD",)),
        PolicySignalDefinition("COMPETITOR", "SIGNAL", "Competitor relationship", "Reviewer may be professionally affiliated with a competitor.", ("PUBLIC_OR_BUSINESS_RECORD",)),
        PolicySignalDefinition("NO_CONFLICT_EVIDENCE", "COUNTER_SIGNAL", "No conflict evidence", "No reliable conflict relationship has been established.", ("RELATIONSHIP_CHECK",)),
    )),
    PolicyDefinition("RD-P04", "Misrepresentation", "Potential material misrepresentation or deceptive account context.", "ACTIVE", "1.0", (
        PolicySignalDefinition("FALSE_ACCOUNT", "SIGNAL", "False account context", "Potentially misleading account identity or context.", ("ACCOUNT_CONTEXT",)),
        PolicySignalDefinition("MISLEADING_DESCRIPTION", "SIGNAL", "Misleading description", "Potential material misrepresentation in the review.", ("RECORD_OR_TIMELINE",)),
        PolicySignalDefinition("VERIFIED_FACTS", "COUNTER_SIGNAL", "Verified facts", "Available records support the material statement.", ("CUSTOMER_RECORD",)),
    )),
    PolicyDefinition("RD-P05", "Off topic", "Potential content unrelated to the business or review experience.", "ACTIVE", "1.0", (
        PolicySignalDefinition("UNRELATED_BUSINESS_TOPIC", "SIGNAL", "Unrelated business topic", "Content appears unrelated to the business.", ("REVIEW_CONTEXT",)),
        PolicySignalDefinition("PERSONAL_RANT", "SIGNAL", "Personal rant", "Content appears primarily unrelated personal commentary.", ("REVIEW_CONTEXT",)),
        PolicySignalDefinition("RELEVANT_EXPERIENCE", "COUNTER_SIGNAL", "Relevant experience", "Review describes a relevant customer experience.", ("CUSTOMER_RECORD_OR_CONTEXT",)),
    )),
    PolicyDefinition("RD-P06", "Advertising", "Potential advertising, promotion, or solicitation in review content.", "ACTIVE", "1.0", (
        PolicySignalDefinition("PROMOTIONAL_CONTENT", "SIGNAL", "Promotional content", "Review contains promotional material.", ("REVIEW_SCREENSHOT",)),
        PolicySignalDefinition("COMMERCIAL_SOLICITATION", "SIGNAL", "Commercial solicitation", "Review solicits commercial contact or business.", ("REVIEW_SCREENSHOT",)),
        PolicySignalDefinition("EXTERNAL_LINK", "SIGNAL", "External link", "Review contains an external link or contact route.", ("REVIEW_SCREENSHOT",)),
        PolicySignalDefinition("NON_COMMERCIAL_CONTENT", "COUNTER_SIGNAL", "Non-commercial content", "Content is not promotional or solicitous.", ("REVIEW_SCREENSHOT",)),
    )),
    PolicyDefinition("RD-P07", "Spam/repetitive", "Potential repetitive, copied, meaningless, or mass-posted content.", "ACTIVE", "1.0", (
        PolicySignalDefinition("DUPLICATE_REVIEW", "SIGNAL", "Duplicate review", "Same or materially duplicated content appears repeatedly.", ("RELATED_REVIEWS",)),
        PolicySignalDefinition("COPIED_CONTENT", "SIGNAL", "Copied content", "Content appears copied across reviews.", ("RELATED_REVIEWS",)),
        PolicySignalDefinition("MEANINGLESS_CONTENT", "SIGNAL", "Meaningless content", "Content appears to lack substantive review content.", ("REVIEW_SCREENSHOT",)),
        PolicySignalDefinition("UNIQUE_CONTENT", "COUNTER_SIGNAL", "Unique content", "Review content is materially distinct.", ("RELATED_REVIEWS",)),
    )),
    PolicyDefinition("RD-P08", "Personal information", "Potential unnecessary identifying or private personal information.", "ACTIVE", "1.0", (
        PolicySignalDefinition("PHONE", "SIGNAL", "Phone number", "Phone number appears in review.", ("REVIEW_SCREENSHOT",)),
        PolicySignalDefinition("EMAIL", "SIGNAL", "Email address", "Email address appears in review.", ("REVIEW_SCREENSHOT",)),
        PolicySignalDefinition("PRIVATE_ID", "SIGNAL", "Private identifier", "Private identifying information appears in review.", ("REVIEW_SCREENSHOT",)),
        PolicySignalDefinition("NO_IDENTIFYING_DATA", "COUNTER_SIGNAL", "No identifying data", "No unnecessary identifying information is present.", ("REVIEW_SCREENSHOT",)),
    )),
    PolicyDefinition("RD-P09", "Harassment", "Potential threats, targeted insults, or personal attacks.", "ACTIVE", "1.0", (
        PolicySignalDefinition("THREAT", "SIGNAL", "Threat", "Threatening language may be present.", ("REVIEW_SCREENSHOT", "MESSAGE_OR_CONTEXT")),
        PolicySignalDefinition("PERSONAL_ATTACK", "SIGNAL", "Personal attack", "Targeted personal attack may be present.", ("REVIEW_SCREENSHOT",)),
        PolicySignalDefinition("NON_TARGETED_CRITICISM", "COUNTER_SIGNAL", "Non-targeted criticism", "Content is criticism of service rather than a personal attack.", ("REVIEW_SCREENSHOT",)),
    )),
    PolicyDefinition("RD-P10", "Extortion", "Potential demand for money, goods, or services linked to review removal.", "ACTIVE", "1.0", (
        PolicySignalDefinition("DEMAND", "SIGNAL", "Demand", "A demand is made in connection with the review.", ("MESSAGE_OR_SCREENSHOT",)),
        PolicySignalDefinition("PAYMENT_OR_BENEFIT_REQUEST", "SIGNAL", "Payment or benefit request", "Money, goods, or services are requested.", ("PAYMENT_RECORD_OR_MESSAGE",)),
        PolicySignalDefinition("REVIEW_REMOVAL_LINK", "SIGNAL", "Review-removal linkage", "The demand is explicitly linked to review removal.", ("MESSAGE_OR_SCREENSHOT",)),
        PolicySignalDefinition("NO_REVIEW_LINK", "COUNTER_SIGNAL", "No review-removal linkage", "No reliable link between demand and review activity.", ("MESSAGE_OR_SCREENSHOT",)),
    )),
)

def policy_catalog() -> tuple[PolicyDefinition, ...]:
    return POLICIES

def build_policy_workspace(organization_id: str, versions: tuple[PolicyVersion, ...] = ()) -> PolicyWorkspace:
    if not organization_id:
        raise ValueError("organization_id is required")
    return PolicyWorkspace(organization_id, POLICIES, versions)

def get_policy(code: str) -> PolicyDefinition:
    for policy in POLICIES:
        if policy.code == code:
            return policy
    raise KeyError(code)

def create_policy_version(code: str, version: str, created_at: str, *, validated_by: str | None = None) -> PolicyVersion:
    policy = get_policy(code)
    status: ValidationStatus = "VALIDATED" if validated_by else "PENDING"
    return PolicyVersion(code, version, policy.signals, created_at, status, validated_by)

def can_edit_policy(role: str) -> bool:
    return role in {"OWNER", "ADMIN", "ANALYST"}

def can_validate_policy(role: str) -> bool:
    return role in {"OWNER", "ADMIN"}

def can_publish_policy(role: str) -> bool:
    return role in {"OWNER", "ADMIN"}

def can_modify_policy(role: str, action: str) -> bool:
    if action == "EDIT":
        return can_edit_policy(role)
    if action in {"VALIDATE", "PUBLISH"}:
        return can_validate_policy(role)
    return False
