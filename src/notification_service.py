"""Application service for controlled notification lifecycle."""
from __future__ import annotations
from typing import Any, Callable
from .notification_delivery import DeliveryError
from .notification_outbox import Notification, create_notification
from .notification_policy import evaluate
from .security_hardening import utc_now

class NotificationService:
    def __init__(self, *, store: Any, repository: Any = None, audit_event: Callable[..., Any] | None = None,
                 delivery_func: Callable[..., Any] | None = None, email_config: dict[str, Any] | None = None,
                 policy_provider: Callable[[str], Any] | None = None):
        self.store, self.repository, self.audit_event = store, repository, audit_event
        self.delivery_func, self.email_config, self.policy_provider = delivery_func, email_config or {}, policy_provider

    def _policy(self, organization_id: str) -> Any:
        return self.policy_provider(organization_id) if self.policy_provider else None

    def _get(self, *, organization_id: str, notification_id: str) -> Notification:
        n=self.store.notifications.get((organization_id,notification_id))
        if n is None and self.repository is not None and hasattr(self.repository,"get_notification"):
            row=self.repository.get_notification(organization_id,notification_id)
            if row:
                n=Notification(**row); self.store.notifications[(organization_id,notification_id)]=n
        if n is None: raise KeyError("notification not found")
        return n

    def queue(self, *, organization_id: str, case_id: str, level: str, channel: str, target: str,
              subject: str, body: str, actor_id: str) -> tuple[Notification,bool]:
        allowed,reason=evaluate(self._policy(organization_id),level=level,channel=channel,now=utc_now())
        if not allowed:
            if self.audit_event: self.audit_event(organization_id,actor_id,"ESCALATION_NOTIFICATION_BLOCKED",f"case:{case_id}",level=level,channel=channel,reason=reason)
            raise PermissionError(reason)
        n=create_notification(organization_id=organization_id,case_id=case_id,level=level,channel=channel,target=target,subject=subject,body=body,actor_id=actor_id)
        for existing in self.store.notifications.values():
            if existing.organization_id==organization_id and existing.dedupe_key==n.dedupe_key and existing.status=="PENDING": return existing,True
        self.store.notifications[(organization_id,n.notification_id)]=n
        if self.repository is not None and hasattr(self.repository,"create_notification"): self.repository.create_notification(organization_id,n.payload())
        if self.audit_event: self.audit_event(organization_id,actor_id,"ESCALATION_NOTIFICATION_QUEUED",f"case:{case_id}",notification_id=n.notification_id,level=level,channel=n.channel)
        return n,False

    def cancel(self, *, organization_id: str, notification_id: str, actor_id: str) -> Notification:
        n=self._get(organization_id=organization_id,notification_id=notification_id)
        if n.status!="PENDING": raise ValueError("only pending notifications can be cancelled")
        n.status="CANCELLED"; n.cancelled_by=actor_id; n.cancelled_at=utc_now().isoformat()
        if self.repository is not None and hasattr(self.repository,"update_notification"): self.repository.update_notification(organization_id,n.payload())
        if self.audit_event: self.audit_event(organization_id,actor_id,"ESCALATION_NOTIFICATION_CANCELLED",f"case:{n.case_id}",notification_id=notification_id)
        return n

    def deliver(self, *, organization_id: str, notification_id: str, actor_id: str) -> tuple[Notification,Any]:
        n=self._get(organization_id=organization_id,notification_id=notification_id)
        allowed,reason=evaluate(self._policy(organization_id),level=n.escalation_level,channel=n.channel,now=utc_now())
        if not allowed:
            if self.audit_event: self.audit_event(organization_id,actor_id,"ESCALATION_NOTIFICATION_BLOCKED",f"case:{n.case_id}",notification_id=notification_id,reason=reason)
            raise PermissionError(reason)
        if self.delivery_func is None: raise DeliveryError("notification delivery is not configured")
        try: result=self.delivery_func(n,email_config=self.email_config)
        except DeliveryError as exc:
            n.delivery_attempts=getattr(n,"delivery_attempts",0)+1; n.last_attempt_at=utc_now().isoformat(); n.delivery_error=str(exc)
            if self.repository is not None and hasattr(self.repository,"record_notification_attempt"): self.repository.record_notification_attempt(organization_id,n.payload())
            if self.audit_event: self.audit_event(organization_id,actor_id,"ESCALATION_NOTIFICATION_DELIVERY_FAILED",f"case:{n.case_id}",notification_id=notification_id,channel=n.channel,error=str(exc))
            raise
        n.status="SENT"; n.sent_by=actor_id; n.sent_at=utc_now().isoformat(); n.delivery_attempts=getattr(n,"delivery_attempts",0)+1; n.last_attempt_at=utc_now().isoformat(); n.delivery_error=None
        if self.repository is not None and hasattr(self.repository,"update_notification"): self.repository.update_notification(organization_id,n.payload())
        if self.audit_event: self.audit_event(organization_id,actor_id,"ESCALATION_NOTIFICATION_DELIVERED",f"case:{n.case_id}",notification_id=notification_id,channel=n.channel,provider=result.provider)
        return n,result

    def mark_sent(self, *, organization_id: str, notification_id: str, actor_id: str) -> Notification:
        n=self._get(organization_id=organization_id,notification_id=notification_id)
        if n.status!="PENDING": raise ValueError("only pending notifications can be marked sent")
        n.status="SENT"; n.sent_by=actor_id; n.sent_at=utc_now().isoformat()
        if self.repository is not None and hasattr(self.repository,"update_notification"): self.repository.update_notification(organization_id,n.payload())
        if self.audit_event: self.audit_event(organization_id,actor_id,"ESCALATION_NOTIFICATION_MARKED_SENT",f"case:{n.case_id}",notification_id=notification_id)
        return n
