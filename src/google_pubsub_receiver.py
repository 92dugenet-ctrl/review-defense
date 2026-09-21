"""V5.9 authenticated Pub/Sub push boundary.
The verifier is deliberately injected: production should use Google's OIDC
JWT verification with issuer/audience checks. An absent verifier rejects pushes.
"""
from __future__ import annotations
import base64,json
from dataclasses import dataclass
from typing import Any,Callable,Mapping
from .google_sync_engine import ReviewEventParser
from .postgres_sync import PostgresSyncRepository, PubSubReceipt

class PubSubAuthenticationError(PermissionError): pass
@dataclass(frozen=True)
class PushResult:
    acknowledged: bool
    duplicate: bool
    job_id: str|None

class AuthenticatedPubSubReceiver:
    def __init__(self, repository: PostgresSyncRepository, verifier: Callable[[str,Mapping[str,Any]], bool]|None=None):
        self.repository=repository; self.verifier=verifier
    def receive(self, organization_id: str, envelope: Mapping[str,Any], *, authorization: str|None=None)->PushResult:
        if self.verifier is None or not authorization or not self.verifier(authorization,envelope):
            raise PubSubAuthenticationError("authenticated Pub/Sub push required")
        message=envelope.get("message") if isinstance(envelope.get("message"),Mapping) else envelope
        data=message.get("data") if isinstance(message,Mapping) else None
        payload=envelope
        if data:
            try:
                raw=base64.b64decode(data,validate=True).decode(); decoded=json.loads(raw)
                payload=decoded if isinstance(decoded,Mapping) else envelope
            except (ValueError,UnicodeError,json.JSONDecodeError) as exc:
                raise ValueError("invalid Pub/Sub data") from exc
        event=ReviewEventParser.parse(payload)
        body={"event_id":event.event_id,"event_type":event.event_type.value,"account_id":event.account_id,"location_id":event.location_id,"review_id":event.review_id}
        receipt=self.repository.claim_event_and_enqueue(organization_id,event.event_id,"google.review.event",body)
        return PushResult(True,not receipt.accepted,receipt.job_id)
