from decimal import Decimal

from src.billing_catalog import get_offer


def test_paypal_catalog_matches_public_one_time_prices():
    assert get_offer("audit_1_9").amount == Decimal("79.00")
    assert get_offer("defense_01").amount == Decimal("49.00")
    assert get_offer("defense_05").amount == Decimal("69.00")
    assert get_offer("pack_enterprise").amount == Decimal("5900.00")


def test_subscription_catalog_is_separate_from_one_time_orders():
    offer = get_offer("monitoring_professional")
    assert offer.kind == "subscription"
    assert offer.amount == Decimal("89.00")
