from dataclasses import dataclass

# Règles d'état de facturation : centralise les statuts reconnus par le domaine. Le catalogue décrit les offres ; les échanges PayPal et les webhooks sont des adaptateurs séparés et ne doivent pas être confondus avec les droits UI.
ACTIVE_STATUSES={'ACTIVE','COMPLETED','APPROVED','TRIALING'}
TERMINAL_STATUSES={'CANCELLED','SUSPENDED','EXPIRED','PAYMENT_FAILED','DENIED','REVERSED','REFUNDED'}
@dataclass(frozen=True)
class PlanPolicy:
 code:str; rank:int; max_cases:int|None; features:frozenset[str]
PLANS={'essential':PlanPolicy('essential',
    1,
    10,
    frozenset({'dashboard',
    'reviews',
    'basic_cases'})),
    'professional':PlanPolicy('professional',
    2,
    100,
    frozenset({'dashboard',
    'reviews',
    'basic_cases',
    'evidence',
    'review_queue',
    'advanced_cases',
    'exports'})),
    'business':PlanPolicy('business',
    3,
    None,
    frozenset({'dashboard',
    'reviews',
    'basic_cases',
    'evidence',
    'review_queue',
    'advanced_cases',
    'exports',
    'team',
    'priority_support'}))}
OFFER_TO_PLAN={'monitoring_essential':'essential','monitoring_professional':'professional','monitoring_business':'business'}
def plan_for_offer(offer_id): return PLANS[OFFER_TO_PLAN.get(str(offer_id),'essential')]
def account_status(subscription):
 if not subscription:return 'trial'
 s=str(subscription.get('status','')).upper()
 if s in ACTIVE_STATUSES:return 'active'
 if s in TERMINAL_STATUSES:return 'restricted'
 return 'pending'
def can_access(plan_code,feature): return feature in PLANS.get(plan_code,PLANS['essential']).features
def public_plans(): return [{'plan':p.code,'rank':p.rank,'max_cases':p.max_cases,'features':sorted(p.features)} for p in PLANS.values()]
