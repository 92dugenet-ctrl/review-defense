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


def test_paypal_order_creation_is_server_priced_and_idempotent(monkeypatch):
    import io, json
    import src.api_server as api_server
    from src.api_server import create_app
    from wsgiref.util import setup_testing_defaults
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "client")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "secret")
    calls=[]
    monkeypatch.setattr(api_server, "paypal_create_order", lambda **kwargs: (calls.append(kwargs) or {"id":"ORDER-1","status":"CREATED"}))
    app=create_app()
    user=app.seed_user(organization_id="billing-org",email="owner@example.com",password="correct horse battery staple")
    from src.security_hardening import Session, hash_token, utc_now
    from datetime import timedelta
    app.store.sessions[hash_token("test-token")]=Session(user.user_id,user.organization_id,user.role,hash_token("test-token"),utc_now()+timedelta(minutes=10),None)
    def call():
        body=json.dumps({"offer_id":"audit_1_9","amount":"1.00"}).encode()
        env={}; setup_testing_defaults(env)
        env.update({"REQUEST_METHOD":"POST","PATH_INFO":"/v1/paypal/orders/create","wsgi.input":io.BytesIO(body),"CONTENT_LENGTH":str(len(body)),"REMOTE_ADDR":"test","HTTP_AUTHORIZATION":"Bearer test-token","HTTP_IDEMPOTENCY_KEY":"billing-key-1"})
        out={}
        def sr(status,headers): out["status"]=int(status.split()[0])
        data=json.loads(b"".join(app(env,sr))); return out["status"],data
    first=call(); second=call()
    assert first[0]==201 and second[0]==201 and first[1]==second[1]
    assert len(calls)==1
    assert calls[0]["amount"]=="79.00"


def test_paypal_capture_is_idempotent(monkeypatch):
    import io, json
    import src.api_server as api_server
    from src.api_server import create_app
    from wsgiref.util import setup_testing_defaults
    monkeypatch.setenv("PAYPAL_CLIENT_ID","client")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET","secret")
    captures=[]
    monkeypatch.setattr(api_server,"paypal_capture_order",lambda order_id:(captures.append(order_id) or {"id":order_id,"status":"COMPLETED"}))
    app=create_app()
    user=app.seed_user(organization_id="billing-org",email="owner@example.com",password="correct horse battery staple")
    app.store.billing["tx-1"]={"id":"tx-1","organization_id":user.organization_id,"user_id":user.user_id,"offer_id":"audit_1_9","kind":"audit","status":"CREATED","currency":"EUR","amount":"79.00","paypal_order_id":"ORDER-2","paypal_subscription_id":None,"metadata":{}}
    from src.security_hardening import Session, hash_token, utc_now
    from datetime import timedelta
    app.store.sessions[hash_token("test-token")]=Session(user.user_id,user.organization_id,user.role,hash_token("test-token"),utc_now()+timedelta(minutes=10),None)
    def call():
        env={}; setup_testing_defaults(env)
        env.update({"REQUEST_METHOD":"POST","PATH_INFO":"/v1/paypal/orders/ORDER-2/capture","wsgi.input":io.BytesIO(b"{}"),"CONTENT_LENGTH":"2","REMOTE_ADDR":"test","HTTP_AUTHORIZATION":"Bearer test-token","HTTP_IDEMPOTENCY_KEY":"capture-key"})
        out={}
        def sr(status,headers): out["status"]=int(status.split()[0])
        data=json.loads(b"".join(app(env,sr))); return out["status"],data
    first=call(); second=call()
    assert first[0]==200 and second[0]==200 and first[1]==second[1]
    assert captures==["ORDER-2"]


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
