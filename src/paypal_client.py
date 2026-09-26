"""Small stdlib-only PayPal REST client for Review Defense."""
from __future__ import annotations
import base64, json, os, urllib.error, urllib.request, uuid

class PayPalError(RuntimeError):
    def __init__(self, message, status=None, payload=None):
        super().__init__(message); self.status=status; self.payload=payload or {}

def configured():
    return bool(os.getenv("PAYPAL_CLIENT_ID","").strip() and os.getenv("PAYPAL_CLIENT_SECRET","").strip())

def configuration_status():
    env=os.getenv("PAYPAL_ENVIRONMENT","sandbox").strip().lower()
    return {"configured":configured(),"environment":env,"client_id_present":bool(os.getenv("PAYPAL_CLIENT_ID","").strip()),"client_secret_present":bool(os.getenv("PAYPAL_CLIENT_SECRET","").strip()),"product_id_present":bool(os.getenv("PAYPAL_PRODUCT_ID","").strip()),"plan_essential_present":bool(os.getenv("PAYPAL_PLAN_ESSENTIAL_ID","").strip()),"plan_professional_present":bool(os.getenv("PAYPAL_PLAN_PROFESSIONAL_ID","").strip()),"plan_business_present":bool(os.getenv("PAYPAL_PLAN_BUSINESS_ID","").strip()),"webhook_id_present":bool(os.getenv("PAYPAL_WEBHOOK_ID","").strip())}

def base_url():
    env=os.getenv("PAYPAL_ENVIRONMENT","sandbox").strip().lower()
    return "https://api-m.sandbox.paypal.com" if env=="sandbox" else "https://api-m.paypal.com"

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
    cid=os.getenv("PAYPAL_CLIENT_ID","").strip(); secret=os.getenv("PAYPAL_CLIENT_SECRET","").strip()
    if not cid or not secret: raise PayPalError("PayPal credentials are not configured")
    raw=base64.b64encode((cid+":"+secret).encode()).decode()
    req=urllib.request.Request(base_url()+"/v1/oauth2/token",data=b"grant_type=client_credentials",
        headers={"Accept":"application/json","Authorization":"Basic "+raw,"Content-Type":"application/x-www-form-urlencoded"},
        method="POST")
    try:
        with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read().decode())["access_token"]
    except urllib.error.HTTPError as exc:
        raise PayPalError("PayPal authentication failed",exc.code) from exc

def create_order(*, offer_id, name, amount, currency, reference_id, return_url, cancel_url):
    token=access_token()
    payload={"intent":"CAPTURE","purchase_units":[{"reference_id":reference_id,"description":name[:127],
        "amount":{"currency_code":currency,"value":amount},"custom_id":offer_id}],
        "application_context":{"brand_name":"Review Defense","landing_page":"LOGIN","user_action":"PAY_NOW",
        "return_url":return_url,"cancel_url":cancel_url}}
    return request_json("POST","/v2/checkout/orders",payload,
        headers={"PayPal-Request-Id":str(uuid.uuid4())},access_token=token)

def capture_order(order_id):
    return request_json("POST",f"/v2/checkout/orders/{order_id}/capture",{},
        headers={"PayPal-Request-Id":str(uuid.uuid4())},access_token=access_token())

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
