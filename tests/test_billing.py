from src.billing_service import account_status,can_access,plan_for_offer

def test_plans(): assert [plan_for_offer(x).code for x in ('monitoring_essential','monitoring_professional','monitoring_business')]==['essential','professional','business']
def test_status(): assert account_status(None)=='trial'; assert account_status({'status':'ACTIVE'})=='active'; assert account_status({'status':'PAYMENT_FAILED'})=='restricted'
def test_access(): assert can_access('essential','reviews'); assert not can_access('essential','exports'); assert can_access('professional','exports'); assert can_access('business','team')

def test_paypal_catalog_uses_only_canonical_buttons():
    from src.billing_catalog import OFFERS, get_offer, public_catalog
    expected_hosted={'6XQ5EXDMKXBF2','ZNRWMCRAFMB4E','QBUG4FU99DHRG','MKMBJPT7JPHCQ'}
    expected_plans={'P-48445016NC686822DNK5DFKI','P-09J30923C56343623NK5DGGI','P-81F64203WR266014XNK5DGZQ'}
    catalog=public_catalog()
    assert set(OFFERS)=={'audit_1_9','audit_10_49','audit_50_99','audit_100_249','audit_250_499','audit_500_999','audit_1000_2499','audit_2500_4999','audit_5000_9999','audit_custom','defense_01','defense_02','defense_03','defense_04','defense_05','defense_standard','defense_plus','defense_complete','monitoring_essential','monitoring_professional','monitoring_business'}
    assert {x['paypal_hosted_button_id'] for x in catalog if x['paypal_hosted_button_id']}==expected_hosted
    assert {x['paypal_plan_id'] for x in catalog if x['paypal_plan_id']}==expected_plans
    assert all(x['kind']!='credit_pack' for x in catalog)
    assert get_offer('monitoring_essential').paypal_plan_id=='P-48445016NC686822DNK5DFKI'
