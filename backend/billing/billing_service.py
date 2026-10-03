from dataclasses import dataclass


ACTIVE_STATUSES = {
    "ACTIVE",
    "COMPLETED",
    "APPROVED",
    "TRIALING",
}

TERMINAL_STATUSES = {
    "CANCELLED",
    "SUSPENDED",
    "EXPIRED",
    "PAYMENT_FAILED",
    "DENIED",
    "REVERSED",
    "REFUNDED",
}


@dataclass(frozen=True)
class PlanPolicy:
    code: str
    rank: int
    max_cases: int | None
    features: frozenset[str]


PLANS = {
    "essential": PlanPolicy(
        "essential",
        1,
        10,
        frozenset({
            "dashboard",
            "reviews",
            "basic_cases",
        }),
    ),
    "professional": PlanPolicy(
        "professional",
        2,
        100,
        frozenset({
            "dashboard",
            "reviews",
            "basic_cases",
            "evidence",
            "review_queue",
            "advanced_cases",
            "exports",
        }),
    ),
    "business": PlanPolicy(
        "business",
        3,
        None,
        frozenset({
            "dashboard",
            "reviews",
            "basic_cases",
            "evidence",
            "review_queue",
            "advanced_cases",
            "exports",
            "team",
            "priority_support",
        }),
    ),
}

OFFER_TO_PLAN = {
    "monitoring_essential": "essential",
    "monitoring_professional": "professional",
    "monitoring_business": "business",
}


def plan_for_offer(offer_id):
    plan_code = OFFER_TO_PLAN.get(
        str(offer_id),
        "essential",
    )
    return PLANS[plan_code]


def account_status(subscription):
    if not subscription:
        return "trial"

    status = str(
        subscription.get("status", "")
    ).upper()

    if status in ACTIVE_STATUSES:
        return "active"

    if status in TERMINAL_STATUSES:
        return "restricted"

    return "pending"


def can_access(plan_code, feature):
    plan = PLANS.get(
        plan_code,
        PLANS["essential"],
    )
    return feature in plan.features


def public_plans():
    return [
        {
            "plan": plan.code,
            "rank": plan.rank,
            "max_cases": plan.max_cases,
            "features": sorted(plan.features),
        }
        for plan in PLANS.values()
    ]
