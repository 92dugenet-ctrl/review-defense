"""Canonical Review Defense billing catalog. Never trust prices supplied by the browser."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Offer:
    offer_id: str
    kind: str
    name_fr: str
    name_en: str
    amount: Decimal | None
    currency: str = "EUR"
    paypal_plan_env: str | None = None

OFFERS = {
    "audit_1_9": Offer("audit_1_9","audit","Audit 1–9 avis","Audit 1–9 reviews",Decimal("79.00")),
    "audit_10_49": Offer("audit_10_49","audit","Audit 10–49 avis","Audit 10–49 reviews",Decimal("149.00")),
    "audit_50_99": Offer("audit_50_99","audit","Audit 50–99 avis","Audit 50–99 reviews",Decimal("249.00")),
    "audit_100_249": Offer("audit_100_249","audit","Audit 100–249 avis","Audit 100–249 reviews",Decimal("399.00")),
    "audit_250_499": Offer("audit_250_499","audit","Audit 250–499 avis","Audit 250–499 reviews",Decimal("599.00")),
    "audit_500_999": Offer("audit_500_999","audit","Audit 500–999 avis","Audit 500–999 reviews",Decimal("899.00")),
    "audit_1000_2499": Offer("audit_1000_2499","audit","Audit 1 000–2 499 avis","Audit 1,000–2,499 reviews",Decimal("1290.00")),
    "audit": Offer("audit","audit_quote","Audit de réputation","Reputation audit",None),
    "defense_01": Offer("defense_01","defense_step","Analyse initiale et qualification","Initial analysis and qualification",Decimal("49.00")),
    "defense_02": Offer("defense_02","defense_step","Préparation du dossier","Case file preparation",Decimal("49.00")),
    "defense_03": Offer("defense_03","defense_step","Première soumission","First submission",Decimal("59.00")),
    "defense_04": Offer("defense_04","defense_step","Relance si nécessaire","Follow-up if necessary",Decimal("49.00")),
    "defense_05": Offer("defense_05","defense_step","Traitement avancé / escalade","Advanced handling / escalation",Decimal("69.00")),
    "pack_starter": Offer("pack_starter","credit_pack","Pack 5 dossiers","5-case pack",Decimal("490.00")),
    "pack_plus": Offer("pack_plus","credit_pack","Pack 10 dossiers","10-case pack",Decimal("990.00")),
    "pack_pro": Offer("pack_pro","credit_pack","Pack 25 dossiers","25-case pack",Decimal("1990.00")),
    "pack_business": Offer("pack_business","credit_pack","Pack 50 dossiers","50-case pack",Decimal("3490.00")),
    "pack_enterprise": Offer("pack_enterprise","credit_pack","Pack 100 dossiers","100-case pack",Decimal("5900.00")),
    "monitoring_essential": Offer("monitoring_essential","subscription","Essential","Essential",Decimal("49.00"),paypal_plan_env="PAYPAL_PLAN_ESSENTIAL_ID"),
    "monitoring_professional": Offer("monitoring_professional","subscription","Professional","Professional",Decimal("89.00"),paypal_plan_env="PAYPAL_PLAN_PROFESSIONAL_ID"),
    "monitoring_business": Offer("monitoring_business","subscription","Business","Business",Decimal("159.00"),paypal_plan_env="PAYPAL_PLAN_BUSINESS_ID"),
}
def get_offer(offer_id: str) -> Offer:
    try: return OFFERS[str(offer_id)]
    except KeyError: raise ValueError("unknown billing offer")
def paypal_plan_id(offer: Offer) -> str | None:
    import os
    return os.getenv(offer.paypal_plan_env, "").strip() if offer.paypal_plan_env else None
