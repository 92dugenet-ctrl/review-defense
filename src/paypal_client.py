"""Minimal PayPal REST client for Review Defense billing.

No third-party HTTP dependency is required. Credentials are server-side only.
The client supports OAuth token acquisition and generic JSON API requests.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any


class PayPalConfigurationError(RuntimeError):
    pass


class PayPalAPIError(RuntimeError):
    def __init__(self, status: int, payload: Any):
        super().__init__(f"PayPal API error ({status})")
        self.status = status
        self.payload = payload


class PayPalClient:
    """Server-side PayPal REST client.

    The client defaults to Sandbox. Production must be enabled explicitly.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        environment: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.client_id = client_id or os.getenv("PAYPAL_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("PAYPAL_CLIENT_SECRET", "")
        self.environment = (environment or os.getenv("PAYPAL_ENV", "sandbox")).lower()
        self.timeout = timeout

        if self.environment not in {"sandbox", "production"}:
            raise PayPalConfigurationError("PAYPAL_ENV must be sandbox or production")

        if not self.client_id or not self.client_secret:
            raise PayPalConfigurationError(
                "PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are required"
            )

    @property
    def base_url(self) -> str:
        if self.environment == "production":
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    def access_token(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        auth = base64.b64encode(credentials).decode("ascii")
        request = urllib.request.Request(
            f"{self.base_url}/v1/oauth2/token",
            data=b"grant_type=client_credentials",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                pass
            raise PayPalAPIError(exc.code, body) from exc

        token = payload.get("access_token")
        if not token:
            raise PayPalAPIError(200, payload)
        return token

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> Any:
        access_token = token or self.access_token()
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method=method.upper(),
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            try:
                body_data = json.loads(body_text)
            except json.JSONDecodeError:
                body_data = body_text
            raise PayPalAPIError(exc.code, body_data) from exc
