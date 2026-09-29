"""Canonical Review Defense billing catalog. Never trust prices supplied by the browser."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

PAYPAL_SUBSCRIPTION_CLIENT_ID = "BAADwFz5aRpmMnNRVADMoONwkWyHzC3Y-l75vTda13-4tfwv2gSa4TdAq_jguOBTz2kBqsU1ARHCQ7nz6k"
PAYPAL_HOSTED_CLIENT_ID = "BAAftx79q4rSHY7vc2aYy_hgx3KB6GB15k__TBghUQyd1_ixXSqv71UHw1RXZvkR4cli25WsSirUKWt7zs"

@dataclass(frozen=True)
class Offer:
    offer_id: str
    kind: str
    name_fr: str
    name_en: str
    amount: Decimal | None
    currency: str = "EUR"
    paypal_plan_id: str | None = None
    paypal_hosted_button_id: str | None = None

OFFERS = {
    "audit_1_9": Offer("audit_1_9","audit","Audit 1–9 avis","Audit 1–9 reviews",Decimal("79.00"),paypal_hosted_button_id="6XQ5EXDMKXBF2"),
    "audit_10_49": Offer("audit_10_49","audit","Audit 10–49 avis","Audit 10–49 reviews",Decimal("149.00"),paypal_hosted_button_id="6XQ5EXDMKXBF2"),
    "audit_50_99": Offer("audit_50_99","audit","Audit 50–99 avis","Audit 50–99 reviews",Decimal("249.00"),paypal_hosted_button_id="6XQ5EXDMKXBF2"),
    "audit_100_249": Offer("audit_100_249","audit","Audit 100–249 avis","Audit 100–249 reviews",Decimal("399.00"),paypal_hosted_button_id="6XQ5EXDMKXBF2"),
    "audit_250_499": Offer("audit_250_499","audit","Audit 250–499 avis","Audit 250–499 reviews",Decimal("599.00"),paypal_hosted_button_id="6XQ5EXDMKXBF2"),
    "audit_500_999": Offer("audit_500_999","audit","Audit 500–999 avis","Audit 500–999 reviews",Decimal("899.00"),paypal_hosted_button_id="ZNRWMCRAFMB4E"),
    "audit_1000_2499": Offer("audit_1000_2499","audit","Audit 1 000–2 499 avis","Audit 1,000–2,499 reviews",Decimal("1290.00"),paypal_hosted_button_id="ZNRWMCRAFMB4E"),
    "audit_2500_4999": Offer("audit_2500_4999","audit","Audit 2 500–4 999 avis","Audit 2,500–4,999 reviews",Decimal("1790.00"),paypal_hosted_button_id="ZNRWMCRAFMB4E"),
    "audit_5000_9999": Offer("audit_5000_9999","audit","Audit 5 000–9 999 avis","Audit 5,000–9,999 reviews",Decimal("2490.00"),paypal_hosted_button_id="ZNRWMCRAFMB4E"),
    "audit_custom": Offer("audit_custom","audit_quote","Audit 10 000+ avis / sur devis","10,000+ reviews / custom quote",None,paypal_hosted_button_id="ZNRWMCRAFMB4E"),
    "defense_01": Offer("defense_01","defense_step","Analyse initiale et qualification","Initial analysis and qualification",Decimal("49.00"),paypal_hosted_button_id="QBUG4FU99DHRG"),
    "defense_02": Offer("defense_02","defense_step","Préparation du dossier","Case file preparation",Decimal("49.00"),paypal_hosted_button_id="QBUG4FU99DHRG"),
    "defense_03": Offer("defense_03","defense_step","Première soumission","First submission",Decimal("59.00"),paypal_hosted_button_id="QBUG4FU99DHRG"),
    "defense_04": Offer("defense_04","defense_step","Relance si nécessaire","Follow-up if necessary",Decimal("49.00"),paypal_hosted_button_id="QBUG4FU99DHRG"),
    "defense_05": Offer("defense_05","defense_step","Traitement avancé / escalade","Advanced handling / escalation",Decimal("69.00"),paypal_hosted_button_id="QBUG4FU99DHRG"),
    "defense_standard": Offer("defense_standard","defense_package","Défense standard d’un avis","Standard review defense",Decimal("149.00"),paypal_hosted_button_id="MKMBJPT7JPHCQ"),
    "defense_plus": Offer("defense_plus","defense_package","Défense renforcée d’un avis","Enhanced review defense",Decimal("249.00"),paypal_hosted_button_id="MKMBJPT7JPHCQ"),
    "defense_complete": Offer("defense_complete","defense_package","Défense complète d’un avis","Complete review defense",Decimal("399.00"),paypal_hosted_button_id="MKMBJPT7JPHCQ"),
    "monitoring_essential": Offer("monitoring_essential","subscription","Essential / Essentiel","Essential / Essentiel",Decimal("49.00"),paypal_plan_id="P-48445016NC686822DNK5DFKI"),
    "monitoring_professional": Offer("monitoring_professional","subscription","Professional / Professionnel","Professional / Professionnel",Decimal("89.00"),paypal_plan_id="P-09J30923C56343623NK5DGGI"),
    "monitoring_business": Offer("monitoring_business","subscription","Business / Entreprise","Business / Entreprise",Decimal("159.00"),paypal_plan_id="P-81F64203WR266014XNK5DGZQ"),
}
def get_offer(offer_id: str) -> Offer:
    try: return OFFERS[str(offer_id)]
    except KeyError: raise ValueError("unknown billing offer")
def paypal_plan_id(offer: Offer) -> str | None:
    """Return the canonical PayPal subscription plan assigned to the offer."""
    return offer.paypal_plan_id

def public_catalog() -> list[dict[str, str | None]]:
    return [{"offer_id":o.offer_id,"kind":o.kind,"name_fr":o.name_fr,"name_en":o.name_en,"amount":str(o.amount) if o.amount is not None else None,"currency":o.currency,"recurring":"true" if o.kind=="subscription" else "false","paypal_plan_id":paypal_plan_id(o),"paypal_hosted_button_id":o.paypal_hosted_button_id} for o in OFFERS.values()]


def paypal_hosted_button_id(offer: Offer) -> str | None:
    return offer.paypal_hosted_button_id
