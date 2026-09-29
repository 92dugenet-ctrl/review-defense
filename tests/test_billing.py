from src.billing_service import account_status,can_access,plan_for_offer

def test_plans(): assert [plan_for_offer(x).code for x in ('monitoring_essential','monitoring_professional','monitoring_business')]==['essential','professional','business']
def test_status(): assert account_status(None)=='trial'; assert account_status({'status':'ACTIVE'})=='active'; assert account_status({'status':'PAYMENT_FAILED'})=='restricted'
def test_access(): assert can_access('essential','reviews'); assert not can_access('essential','exports'); assert can_access('professional','exports'); assert can_access('business','team')
def test_paypal_ids():
 from src.billing_catalog import get_offer
 assert get_offer('monitoring_essential').paypal_plan_id and get_offer('defense_standard').paypal_hosted_button_id
