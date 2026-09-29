from src.billing_service import account_status,can_access,plan_for_offer

def test_plans(): assert [plan_for_offer(x).code for x in ('monitoring_essential','monitoring_professional','monitoring_business')]==['essential','professional','business']
def test_status(): assert account_status(None)=='trial'; assert account_status({'status':'ACTIVE'})=='active'; assert account_status({'status':'PAYMENT_FAILED'})=='restricted'
def test_access(): assert can_access('essential','reviews'); assert not can_access('essential','exports'); assert can_access('professional','exports'); assert can_access('business','team')
def test_paypal_ids(monkeypatch):
 from src.billing_catalog import get_offer, paypal_plan_id
 monkeypatch.setenv("PAYPAL_PLAN_ESSENTIAL_ID", "P-env-essential")
 assert paypal_plan_id(get_offer("monitoring_essential")) == "P-env-essential"
 assert get_offer("defense_standard").paypal_hosted_button_id

def test_paypal_plan_catalog_prefers_environment(monkeypatch):
 from src.billing_catalog import get_offer, public_catalog
 monkeypatch.setenv("PAYPAL_PLAN_PROFESSIONAL_ID", "P-env-professional")
 item = next(x for x in public_catalog() if x["offer_id"] == "monitoring_professional")
 assert item["paypal_plan_id"] == "P-env-professional"
