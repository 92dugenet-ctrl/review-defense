from decimal import Decimal

import pytest

from src.billing import PLANS, SubscriptionStatus, loyalty_price
from src.paypal_client import PayPalClient, PayPalConfigurationError


def test_paypal_defaults_to_sandbox(monkeypatch):
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "sandbox-client")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "sandbox-secret")
    monkeypatch.delenv("PAYPAL_ENV", raising=False)

    client = PayPalClient()
    assert client.environment == "sandbox"
    assert client.base_url == "https://api-m.sandbox.paypal.com"


def test_paypal_production_endpoint(monkeypatch):
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "live-client")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "live-secret")
    monkeypatch.setenv("PAYPAL_ENV", "production")

    client = PayPalClient()
    assert client.base_url == "https://api-m.paypal.com"


def test_paypal_requires_credentials(monkeypatch):
    monkeypatch.delenv("PAYPAL_CLIENT_ID", raising=False)
    monkeypatch.delenv("PAYPAL_CLIENT_SECRET", raising=False)

    with pytest.raises(PayPalConfigurationError):
        PayPalClient()


def test_loyalty_schedule():
    plan = PLANS["professional"]
    assert loyalty_price(plan, 0) == Decimal("89.00")
    assert loyalty_price(plan, 4) == Decimal("84.00")
    assert loyalty_price(plan, 7) == Decimal("79.00")
    assert loyalty_price(plan, 13) == Decimal("74.00")
    assert loyalty_price(plan, 25) == Decimal("69.00")


def test_reactivation_never_reuses_old_loyalty_price():
    plan = PLANS["business"]
    assert plan.public_price == Decimal("159.00")
    assert plan.loyalty_floor == Decimal("119.00")
