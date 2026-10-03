"""Small stdlib-only PayPal REST client for Review Defense."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request


class PayPalError(RuntimeError):
    def __init__(
        self,
        message,
        status=None,
        payload=None,
    ):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


def configured():
    client_id = PAYPAL_SUBSCRIPTION_CLIENT_ID
    client_secret = os.getenv(
        "PAYPAL_CLIENT_SECRET",
        "",
    ).strip()

    return bool(client_id and client_secret)


def configuration_status():
    client_secret = os.getenv(
        "PAYPAL_CLIENT_SECRET",
        "",
    ).strip()
    webhook_id = os.getenv(
        "PAYPAL_WEBHOOK_ID",
        "",
    ).strip()

    return {
        "configured": configured(),
        "environment": "live",
        "client_id_present": bool(
            PAYPAL_SUBSCRIPTION_CLIENT_ID
        ),
        "client_secret_present": bool(client_secret),
        "webhook_id_present": bool(webhook_id),
    }


def base_url():
    return "https://api-m.paypal.com"


def request_json(
    method,
    path,
    payload=None,
    headers=None,
    access_token=None,
):
    body = (
        json.dumps(payload).encode()
        if payload is not None
        else None
    )
    request_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if headers:
        request_headers.update(headers)

    if access_token:
        request_headers["Authorization"] = (
            "Bearer " + access_token
        )

    request = urllib.request.Request(
        base_url() + path,
        data=body,
        headers=request_headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:
            raw_response = response.read()

            if not raw_response:
                return {}

            return json.loads(raw_response.decode())

    except urllib.error.HTTPError as error:
        raw_response = error.read()

        try:
            data = json.loads(raw_response.decode())
        except Exception:
            data = {
                "raw": raw_response.decode(
                    errors="replace"
                )
            }

        raise PayPalError(
            data.get("message", "PayPal request failed"),
            error.code,
            data,
        ) from error

    except urllib.error.URLError as error:
        raise PayPalError(
            "PayPal is unreachable"
        ) from error


def access_token():
    client_id = PAYPAL_SUBSCRIPTION_CLIENT_ID
    client_secret = os.getenv(
        "PAYPAL_CLIENT_SECRET",
        "",
    ).strip()

    if not client_id or not client_secret:
        raise PayPalError(
            "PayPal credentials are not configured"
        )

    credentials = base64.b64encode(
        (client_id + ":" + client_secret).encode()
    ).decode()
    request = urllib.request.Request(
        base_url() + "/v1/oauth2/token",
        data=b"grant_type=client_credentials",
        headers={
            "Accept": "application/json",
            "Authorization": "Basic " + credentials,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:
            data = json.loads(response.read().decode())
            return data["access_token"]

    except urllib.error.HTTPError as error:
        raw_response = error.read()

        try:
            data = json.loads(raw_response.decode())
        except Exception:
            data = {}

        raise PayPalError(
            "PayPal authentication failed",
            error.code,
            data,
        ) from error


def verify_webhook(*, raw_body, headers):
    webhook_id = os.getenv(
        "PAYPAL_WEBHOOK_ID",
        "",
    ).strip()

    if not webhook_id:
        raise PayPalError(
            "PAYPAL_WEBHOOK_ID is not configured"
        )

    payload = json.loads(raw_body.decode("utf-8"))
    verification_payload = {
        "transmission_id": headers.get(
            "paypal-transmission-id",
            "",
        ),
        "transmission_time": headers.get(
            "paypal-transmission-time",
            "",
        ),
        "cert_url": headers.get(
            "paypal-cert-url",
            "",
        ),
        "auth_algo": headers.get(
            "paypal-auth-algo",
            "",
        ),
        "transmission_sig": headers.get(
            "paypal-transmission-sig",
            "",
        ),
        "webhook_id": webhook_id,
        "webhook_event": payload,
    }
    result = request_json(
        "POST",
        "/v1/notifications/verify-webhook-signature",
        verification_payload,
        access_token=access_token(),
    )

    return (
        result.get("verification_status") == "SUCCESS",
        payload,
    )
