"""Small stdlib-only PayPal REST client for Review Defense."""
from __future__ import annotations
import base64, json, os, urllib.error, urllib.request

class PayPalError(RuntimeError):
    def __init__(self, message, status=None, payload=None):
        super().__init__(message); self.status=status; self.payload=payload or {}

def configured():
    return bool(PAYPAL_SUBSCRIPTION_CLIENT_ID and os.getenv("PAYPAL_CLIENT_SECRET","").strip())

def configuration_status():
    return {"configured":configured(),"environment":"live","client_id_present":bool(PAYPAL_SUBSCRIPTION_CLIENT_ID),"client_secret_present":bool(os.getenv("PAYPAL_CLIENT_SECRET","").strip()),"webhook_id_present":bool(os.getenv("PAYPAL_WEBHOOK_ID","").strip())}

def base_url():
    return "https://api-m.paypal.com"

def request_json(method, path, payload=None, headers=None, access_token=None):
    body=json.dumps(payload).encode() if payload is not None else None
    h={"Accept":"application/json","Content-Type":"application/json"}
    if headers: h.update(headers)
    if access_token: h["Authorization"]="Bearer "+access_token
    req=urllib.request.Request(base_url()+path,data=body,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read(); return json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as exc:
        raw=exc.read()
        try: data=json.loads(raw.decode())
        except Exception: data={"raw":raw.decode(errors="replace")}
        raise PayPalError(data.get("message","PayPal request failed"),exc.code,data) from exc
    except urllib.error.URLError as exc:
        raise PayPalError("PayPal is unreachable") from exc

def access_token():
    cid=PAYPAL_SUBSCRIPTION_CLIENT_ID; secret=os.getenv("PAYPAL_CLIENT_SECRET","").strip()
    if not cid or not secret: raise PayPalError("PayPal credentials are not configured")
    raw=base64.b64encode((cid+":"+secret).encode()).decode()
    req=urllib.request.Request(base_url()+"/v1/oauth2/token",data=b"grant_type=client_credentials",
        headers={"Accept":"application/json","Authorization":"Basic "+raw,"Content-Type":"application/x-www-form-urlencoded"},
        method="POST")
    try:
        with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read().decode())["access_token"]
    except urllib.error.HTTPError as exc:
        raw=exc.read()
        try: data=json.loads(raw.decode())
        except Exception: data={}
        raise PayPalError("PayPal authentication failed",exc.code,data) from exc

def verify_webhook(*,raw_body,headers):
    webhook_id=os.getenv("PAYPAL_WEBHOOK_ID","").strip()
    if not webhook_id: raise PayPalError("PAYPAL_WEBHOOK_ID is not configured")
    payload=json.loads(raw_body.decode("utf-8"))
    data={"transmission_id":headers.get("paypal-transmission-id",""),
          "transmission_time":headers.get("paypal-transmission-time",""),
          "cert_url":headers.get("paypal-cert-url",""),
          "auth_algo":headers.get("paypal-auth-algo",""),
          "transmission_sig":headers.get("paypal-transmission-sig",""),
          "webhook_id":webhook_id,"webhook_event":payload}
    result=request_json("POST","/v1/notifications/verify-webhook-signature",data,access_token=access_token())
    return result.get("verification_status")=="SUCCESS", payload

# Compatibility client copied from feature/paypal-billing-v1: supports Sandbox and Production.
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
