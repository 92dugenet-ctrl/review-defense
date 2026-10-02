"""Review Defense billing domain primitives.

PayPal remains the payment provider. This module remains the application
source of truth for plans, entitlements, loyalty pricing and one-off steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class SubscriptionStatus(str, Enum):
    TRIALING = "TRIALING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    PAUSED = "PAUSED"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"
    UNPAID = "UNPAID"


class OneOffType(str, Enum):
    AUDIT = "AUDIT"
    DEFENSE_INITIAL = "DEFENSE_INITIAL"
    DEFENSE_STEP = "DEFENSE_STEP"
    DEFENSE_PACK = "DEFENSE_PACK"


class DefenseStep(str, Enum):
    INITIAL_ANALYSIS = "INITIAL_ANALYSIS"
    PREPARATION = "PREPARATION"
    SUBMISSION = "SUBMISSION"
    FOLLOW_UP = "FOLLOW_UP"
    ADVANCED_TREATMENT = "ADVANCED_TREATMENT"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class Plan:
    code: str
    public_price: Decimal
    loyalty_floor: Decimal
    max_locations: int | None
    max_users: int | None
    max_reviews_per_location: int | None
    responses: bool
    advanced_analysis: bool


PLANS = {
    "essential": Plan("essential", Decimal("49.00"), Decimal("37.00"), 1, 1, 500, False, False),
    "professional": Plan("professional", Decimal("89.00"), Decimal("69.00"), 3, 5, 2500, True, True),
    "business": Plan("business", Decimal("159.00"), Decimal("119.00"), 10, 15, 10000, True, True),
}


def loyalty_price(plan: Plan, continuous_months: int) -> Decimal:
    """Return the current monthly price from the approved loyalty schedule."""
    steps = {
        "essential": (Decimal("49.00"), Decimal("46.00"), Decimal("43.00"), Decimal("40.00"), Decimal("37.00")),
        "professional": (Decimal("89.00"), Decimal("84.00"), Decimal("79.00"), Decimal("74.00"), Decimal("69.00")),
        "business": (Decimal("159.00"), Decimal("149.00"), Decimal("139.00"), Decimal("129.00"), Decimal("119.00")),
    }
    prices = steps[plan.code]
    if continuous_months <= 3:
        return prices[0]
    if continuous_months <= 6:
        return prices[1]
    if continuous_months <= 12:
        return prices[2]
    if continuous_months <= 24:
        return prices[3]
    return prices[4]


def assert_reactivation_uses_public_price(plan: Plan) -> Decimal:
    """New subscriptions never inherit an old loyalty price."""
    return plan.public_price
