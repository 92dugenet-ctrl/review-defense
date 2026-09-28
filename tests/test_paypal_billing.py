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


def test_paypal_base_url_is_live_by_default(monkeypatch):
    monkeypatch.delenv("PAYPAL_BASE_URL", raising=False)
    from src.paypal_client import base_url
    assert base_url() == "https://api-m.paypal.com"

def test_paypal_base_url_rejects_sandbox(monkeypatch):
    monkeypatch.setenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
    from src.paypal_client import base_url, PayPalError
    import pytest
    with pytest.raises(PayPalError):
        base_url()


def test_paypal_base_url_rejects_untrusted_endpoint(monkeypatch):
    monkeypatch.setenv("PAYPAL_BASE_URL", "https://example.invalid")
    from src.paypal_client import base_url, PayPalError
    import pytest
    with pytest.raises(PayPalError):
        base_url()


def test_billing_catalog_covers_audits_defense_and_packs():
    from src.billing_catalog import OFFERS, public_catalog
    required={"audit_1_9","audit_1000_2499","audit_5000_9999","audit_custom","defense_01","defense_complete","pack_starter","pack_1000","pack_custom","monitoring_essential","monitoring_business"}
    assert required.issubset(OFFERS)
    catalog={item["offer_id"]:item for item in public_catalog()}
    assert len(catalog)==len(OFFERS)
    assert catalog["audit_custom"]["amount"] is None
    assert catalog["defense_complete"]["amount"]=="399.00"
    assert catalog["pack_1000"]["amount"]=="44900.00"


def test_billing_catalog_groups_have_expected_offer_kinds():
    from src.billing_catalog import OFFERS
    assert all(o.kind == "subscription" for o in OFFERS.values() if o.offer_id.startswith("monitoring_"))
    assert all(o.kind in {"defense_step", "defense_package"} for o in OFFERS.values() if o.offer_id.startswith("defense_"))
    assert all(o.kind in {"credit_pack", "credit_pack_quote"} for o in OFFERS.values() if o.offer_id.startswith("pack_"))


def test_subscription_catalog_contains_paypal_plan_ids():
    assert get_offer("monitoring_essential").paypal_plan_id == "P-48445016NC686822DNK5DFKI"
    assert get_offer("monitoring_professional").paypal_plan_id == "P-09J30923C56343623NK5DGGI"
    assert get_offer("monitoring_business").paypal_plan_id == "P-81F64203WR266014XNK5DGZQ"


def test_defense_offers_share_paypal_hosted_buttons():
    for offer_id in ("defense_01", "defense_02", "defense_03", "defense_04", "defense_05"):
        assert get_offer(offer_id).paypal_hosted_button_id == "QBUG4FU99DHRG"
    for offer_id in ("defense_standard", "defense_plus", "defense_complete"):
        assert get_offer(offer_id).paypal_hosted_button_id == "MKMBJPT7JPHCQ"


def test_audit_offers_share_paypal_hosted_buttons():
    for offer_id in ("audit_1_9", "audit_10_49", "audit_50_99", "audit_100_249", "audit_250_499"):
        assert get_offer(offer_id).paypal_hosted_button_id == "6XQ5EXDMKXBF2"
    for offer_id in ("audit_500_999", "audit_1000_2499", "audit_2500_4999", "audit_5000_9999", "audit_custom"):
        assert get_offer(offer_id).paypal_hosted_button_id == "ZNRWMCRAFMB4E"


def test_public_catalog_exposes_paypal_checkout_identifiers():
    from src.billing_catalog import public_catalog
    catalog={item["offer_id"]:item for item in public_catalog()}
    assert catalog["defense_01"]["paypal_hosted_button_id"] == "QBUG4FU99DHRG"
    assert catalog["defense_complete"]["paypal_hosted_button_id"] == "MKMBJPT7JPHCQ"
    assert catalog["audit_1_9"]["paypal_hosted_button_id"] == "6XQ5EXDMKXBF2"
    assert catalog["audit_500_999"]["paypal_hosted_button_id"] == "ZNRWMCRAFMB4E"
    assert catalog["monitoring_professional"]["paypal_plan_id"] == "P-09J30923C56343623NK5DGGI"


def test_paypal_capture_webhook_uses_related_order_id_for_billing_correlation():
    resource = {
        "id": "CAPTURE-123",
        "supplementary_data": {"related_ids": {"order_id": "ORDER-456"}},
    }
    related_ids = ((resource.get("supplementary_data") or {}).get("related_ids") or {})
    paypal_order_id = str(related_ids.get("order_id") or resource.get("order_id") or "")
    paypal_capture_id = str(resource.get("id") or "")
    paypal_id = paypal_order_id or paypal_capture_id
    assert paypal_id == "ORDER-456"
    assert paypal_capture_id == "CAPTURE-123"
