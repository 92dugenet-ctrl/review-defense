#!/usr/bin/env python3
"""Provision Review Defense PayPal Sandbox product and subscription plans.

This script is intentionally separate from the application checkout integration.
It uses only the PayPal REST API and environment variables; no credentials are
stored in the repository and no frontend code is changed.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from urllib import error, parse, request


DEFAULT_BASE_URL = "https://api-m.sandbox.paypal.com"
OUTPUT_PATH = Path("paypal-sandbox-config.json")

PLANS = (
    {
        "key": "essential",
        "name": "Review Defense — Essential",
        "description": "Surveillance Google Business / Google Business monitoring",
        "amount": "49.00",
    },
    {
        "key": "professional",
        "name": "Review Defense — Professional",
        "description": "Surveillance avancée + réponses / Advanced monitoring + responses",
        "amount": "89.00",
    },
    {
        "key": "business",
        "name": "Review Defense — Business",
        "description": "Surveillance avancée + réponses + multi-sites / Advanced monitoring + responses + multi-site",
        "amount": "159.00",
    },
)


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


def request_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


class PayPalClient:
    def __init__(self) -> None:
        self.client_id = required("PAYPAL_CLIENT_ID")
        self.client_secret = required("PAYPAL_CLIENT_SECRET")
        self.base_url = (
            os.getenv("PAYPAL_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
        )
        if self.base_url not in {DEFAULT_BASE_URL, "https://api-m.paypal.com"}:
            raise RuntimeError("PAYPAL_BASE_URL doit pointer vers une API PayPal officielle")
        if os.getenv("PAYPAL_ENVIRONMENT", "sandbox").strip().lower() != "sandbox":
            raise RuntimeError("Le provisioning Sandbox ne peut utiliser que l'API Sandbox PayPal")

    def access_token(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        body = parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/v1/oauth2/token",
            data=body,
            method="POST",
            headers={
                "Authorization": "Basic " + __import__("base64").b64encode(credentials).decode(),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )
        return self._send(req).get("access_token", "")

    def api(self, method: str, path: str, payload: dict | None = None) -> dict:
        token = self.access_token()
        data = None
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers=headers,
        )
        req.add_header("PayPal-Request-Id", request_id("REVIEW-DEFENSE"))
        req.add_header("Prefer", "return=representation")
        return self._send(req)

    @staticmethod
    def _send(req: request.Request) -> dict:
        try:
            with request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw}
            details = payload.get("details") or []
            detail_text = "; ".join(
                f"{d.get('issue', 'ERROR')}: {d.get('description', '')}".strip(": ")
                for d in details
            )
            message = detail_text or payload.get("message") or payload.get("error_description") or raw
            raise RuntimeError(f"PayPal HTTP {exc.code}: {message}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Connexion PayPal impossible : {exc.reason}") from exc


def create_product(client: PayPalClient) -> str:
    existing = os.getenv("PAYPAL_PRODUCT_ID", "").strip()
    if existing:
        print(f"Produit existant utilisé : {existing}")
        return existing

    product = client.api(
        "POST",
        "/v1/catalogs/products",
        {
            "name": "Review Defense",
            "description": (
                "Service de surveillance et de défense des avis Google / "
                "Google review monitoring and defense service"
            ),
            "type": "SERVICE",
            "category": "SOFTWARE",
            "home_url": os.getenv(
                "PAYPAL_HOME_URL", "https://review-defense.com"
            ).strip(),
        },
    )
    product_id = product["id"]
    print(f"Produit créé : {product_id}")
    return product_id


def create_plan(client: PayPalClient, product_id: str, plan: dict) -> dict:
    env_key = f"PAYPAL_PLAN_{plan['key'].upper()}_ID"
    existing = os.getenv(env_key, "").strip()
    if existing:
        print(f"Plan {plan['key']} existant utilisé : {existing}")
        return {
            "key": plan["key"],
            "plan_id": existing,
            "amount_eur": plan["amount"],
            "status": "EXISTING",
        }

    created = client.api(
        "POST",
        "/v1/billing/plans",
        {
            "product_id": product_id,
            "name": plan["name"],
            "description": plan["description"],
            "billing_cycles": [
                {
                    "frequency": {
                        "interval_unit": "MONTH",
                        "interval_count": 1,
                    },
                    "tenure_type": "REGULAR",
                    "sequence": 1,
                    "total_cycles": 0,
                    "pricing_scheme": {
                        "fixed_price": {
                            "value": plan["amount"],
                            "currency_code": "EUR",
                        }
                    },
                }
            ],
            "payment_preferences": {
                "auto_bill_outstanding": True,
                "setup_fee_failure_action": "CONTINUE",
                "payment_failure_threshold": 1,
            },
        },
    )

    plan_id = created["id"]
    status = created.get("status", "CREATED")
    if status != "ACTIVE":
        client.api("POST", f"/v1/billing/plans/{plan_id}/activate")
        status = "ACTIVE"

    print(f"Plan {plan['key']} créé/activé : {plan_id} — {plan['amount']} EUR/mois")
    return {
        "key": plan["key"],
        "plan_id": plan_id,
        "amount_eur": plan["amount"],
        "status": status,
    }


def provision_webhook(client: PayPalClient) -> str:
    existing=os.getenv("PAYPAL_WEBHOOK_ID","").strip()
    if existing:
        print(f"Webhook existant utilisé : {existing}")
        return existing
    url=os.getenv("PAYPAL_HOME_URL","https://review-defense.com").strip().rstrip("/")+"/v1/paypal/webhook"
    try:
        current=client.api("GET","/v1/notifications/webhooks")
        for item in current.get("webhooks",[]):
            if item.get("url")==url:
                print(f"Webhook existant trouvé : {item.get('id')}")
                return item.get("id","")
    except RuntimeError:
        pass
    created=client.api("POST","/v1/notifications/webhooks",{
        "url":url,
        "event_types":[{"name":x} for x in (
            "CHECKOUT.ORDER.COMPLETED","PAYMENT.CAPTURE.COMPLETED","PAYMENT.CAPTURE.DENIED",
            "PAYMENT.SALE.COMPLETED","PAYMENT.SALE.REFUNDED","PAYMENT.SALE.REVERSED",
            "BILLING.SUBSCRIPTION.ACTIVATED","BILLING.SUBSCRIPTION.UPDATED",
            "BILLING.SUBSCRIPTION.CANCELLED","BILLING.SUBSCRIPTION.SUSPENDED",
            "BILLING.SUBSCRIPTION.EXPIRED","BILLING.SUBSCRIPTION.PAYMENT.FAILED"
        )]
    })
    wid=created.get("id","")
    print(f"Webhook créé : {wid} → {url}")
    return wid

def main() -> int:
    if os.getenv("PAYPAL_ENVIRONMENT", "sandbox").strip().lower() != "sandbox":
        raise RuntimeError(
            "Ce script est volontairement limité au Sandbox. "
            "PAYPAL_ENVIRONMENT doit être 'sandbox'."
        )

    print("=== Review Defense — PayPal Sandbox provisioning ===")
    client = PayPalClient()
    product_id = create_product(client)
    plans = [create_plan(client, product_id, plan) for plan in PLANS]
    webhook_id = provision_webhook(client)

    output = {
        "environment": "sandbox",
        "product_id": product_id,
        "currency": "EUR",
        "plans": plans,
        "webhook_id": webhook_id,
        "webhook_url": os.getenv("PAYPAL_HOME_URL", "https://review-defense.com").strip().rstrip("/") + "/v1/paypal/webhook",
        "generated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "next_step": "Wire these IDs into the Review Defense billing integration.",
        "loyalty_pricing": "Managed per subscription in the application; not encoded as a global plan-price mutation.",
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Configuration générée : {OUTPUT_PATH}")
    print("Aucun secret PayPal n'a été écrit dans ce fichier.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        raise SystemExit(1)
