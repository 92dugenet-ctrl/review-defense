"""Application service for the controlled notification lifecycle."""

from __future__ import annotations

from typing import Any, Callable

from .notification_delivery import DeliveryError
from .notification_observability import build_notification_metrics
from .notification_outbox import Notification, create_notification
from .notification_policy import evaluate, validate_policy
from .notification_worker import NotificationWorker, WorkerResult
from .security_hardening import utc_now


class NotificationService:
    def __init__(
        self,
        *,
        store: Any,
        repository: Any = None,
        audit_event: Callable[..., Any] | None = None,
        delivery_func: Callable[..., Any] | None = None,
        email_config: dict[str, Any] | None = None,
        policy_provider: Callable[[str], Any] | None = None,
        worker: NotificationWorker | None = None,
    ):
        self.store = store
        self.repository = repository
        self.audit_event = audit_event
        self.delivery_func = delivery_func
        self.email_config = email_config or {}
        self.policy_provider = policy_provider
        self.worker = worker or NotificationWorker(
            delivery_func=delivery_func,
            email_config=self.email_config,
        )

    def _policy(self, organization_id: str) -> Any:
        if self.policy_provider:
            return self.policy_provider(organization_id)
        return None

    def policy_for_organization(self, *, organization_id: str) -> tuple[Any, bool]:
        policies = self.store.notification_policies
        if organization_id not in policies and self._has_repository_method(
            "get_notification_policy"
        ):
            row = self.repository.get_notification_policy(organization_id)
            if row:
                policies[organization_id] = validate_policy(organization_id, row)

        configured = organization_id in policies
        return (
            policies.get(organization_id) or validate_policy(organization_id, {}),
            configured,
        )

    def set_policy(
        self, *, organization_id: str, payload: dict[str, Any], actor_id: str
    ) -> Any:
        policy = validate_policy(organization_id, payload)
        self.store.notification_policies[organization_id] = policy
        if self._has_repository_method("upsert_notification_policy"):
            self.repository.upsert_notification_policy(
                organization_id, policy.payload()
            )
        self._audit(
            organization_id,
            actor_id,
            "NOTIFICATION_POLICY_UPDATED",
            f"organization:{organization_id}",
            policy=policy.payload(),
        )
        return policy

    def list_for_organization(
        self,
        *,
        organization_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._has_repository_method("list_notifications"):
            for row in self.repository.list_notifications(organization_id, status):
                notification = Notification(**row)
                self.store.notifications[
                    (organization_id, notification.notification_id)
                ] = notification

        notifications = [
            notification.payload()
            for (organization, _), notification in self.store.notifications.items()
            if organization == organization_id
            and (status is None or notification.status == status)
        ]
        notifications.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return notifications

    def metrics_for_organization(self, *, organization_id: str) -> dict[str, Any]:
        self.list_for_organization(organization_id=organization_id)
        return build_notification_metrics(
            self.store.notifications.values(),
            self.store.audit,
            organization_id=organization_id,
        )

    def run_worker(
        self, *, organization_id: str, limit: int, actor_id: str
    ) -> WorkerResult:
        self._load_notifications(organization_id, status="PENDING")
        notifications = [
            notification
            for (organization, _), notification in self.store.notifications.items()
            if organization == organization_id
        ]

        def persist(notification: Notification) -> None:
            if self._has_repository_method("update_notification"):
                self.repository.update_notification(
                    organization_id, notification.payload()
                )

        policy, _ = self.policy_for_organization(organization_id=organization_id)
        self.worker.policy = policy
        result = self.worker.run_once(
            notifications,
            organization_id=organization_id,
            limit=limit,
            actor_id=actor_id,
            persist=persist,
            audit=self.audit_event,
        )
        self._audit(
            organization_id,
            actor_id,
            "NOTIFICATION_WORKER_RUN",
            "notifications",
            processed=result.processed,
            sent=result.sent,
            retried=result.retried,
            dead_lettered=result.dead_lettered,
            skipped=result.skipped,
        )
        return result

    def queue(
        self,
        *,
        organization_id: str,
        case_id: str,
        level: str,
        channel: str,
        target: str,
        subject: str,
        body: str,
        actor_id: str,
    ) -> tuple[Notification, bool]:
        allowed, reason = evaluate(
            self._policy(organization_id),
            level=level,
            channel=channel,
            now=utc_now(),
        )
        if not allowed:
            self._audit(
                organization_id,
                actor_id,
                "ESCALATION_NOTIFICATION_BLOCKED",
                f"case:{case_id}",
                level=level,
                channel=channel,
                reason=reason,
            )
            raise PermissionError(reason)

        notification = create_notification(
            organization_id=organization_id,
            case_id=case_id,
            level=level,
            channel=channel,
            target=target,
            subject=subject,
            body=body,
            actor_id=actor_id,
        )
        for existing in self.store.notifications.values():
            if (
                existing.organization_id == organization_id
                and existing.dedupe_key == notification.dedupe_key
                and existing.status == "PENDING"
            ):
                return existing, True

        self.store.notifications[(organization_id, notification.notification_id)] = (
            notification
        )
        if self._has_repository_method("create_notification"):
            self.repository.create_notification(organization_id, notification.payload())
        self._audit(
            organization_id,
            actor_id,
            "ESCALATION_NOTIFICATION_QUEUED",
            f"case:{case_id}",
            notification_id=notification.notification_id,
            level=level,
            channel=notification.channel,
        )
        return notification, False

    def cancel(
        self, *, organization_id: str, notification_id: str, actor_id: str
    ) -> Notification:
        notification = self._get(
            organization_id=organization_id, notification_id=notification_id
        )
        if notification.status != "PENDING":
            raise ValueError("only pending notifications can be cancelled")
        notification.status = "CANCELLED"
        notification.cancelled_by = actor_id
        notification.cancelled_at = utc_now().isoformat()
        self._save(notification)
        self._audit(
            organization_id,
            actor_id,
            "ESCALATION_NOTIFICATION_CANCELLED",
            f"case:{notification.case_id}",
            notification_id=notification_id,
        )
        return notification

    def deliver(
        self, *, organization_id: str, notification_id: str, actor_id: str
    ) -> tuple[Notification, Any]:
        notification = self._get(
            organization_id=organization_id, notification_id=notification_id
        )
        allowed, reason = evaluate(
            self._policy(organization_id),
            level=notification.escalation_level,
            channel=notification.channel,
            now=utc_now(),
        )
        if not allowed:
            self._audit(
                organization_id,
                actor_id,
                "ESCALATION_NOTIFICATION_BLOCKED",
                f"case:{notification.case_id}",
                notification_id=notification_id,
                reason=reason,
            )
            raise PermissionError(reason)
        if self.delivery_func is None:
            raise DeliveryError("notification delivery is not configured")

        try:
            result = self.delivery_func(notification, email_config=self.email_config)
        except DeliveryError as error:
            notification.delivery_attempts = (
                getattr(notification, "delivery_attempts", 0) + 1
            )
            notification.last_attempt_at = utc_now().isoformat()
            notification.delivery_error = str(error)
            if self._has_repository_method("record_notification_attempt"):
                self.repository.record_notification_attempt(
                    organization_id, notification.payload()
                )
            self._audit(
                organization_id,
                actor_id,
                "ESCALATION_NOTIFICATION_DELIVERY_FAILED",
                f"case:{notification.case_id}",
                notification_id=notification_id,
                channel=notification.channel,
                error=str(error),
            )
            raise

        notification.status = "SENT"
        notification.sent_by = actor_id
        notification.sent_at = utc_now().isoformat()
        notification.delivery_attempts = (
            getattr(notification, "delivery_attempts", 0) + 1
        )
        notification.last_attempt_at = utc_now().isoformat()
        notification.delivery_error = None
        self._save(notification)
        self._audit(
            organization_id,
            actor_id,
            "ESCALATION_NOTIFICATION_DELIVERED",
            f"case:{notification.case_id}",
            notification_id=notification_id,
            channel=notification.channel,
            provider=result.provider,
        )
        return notification, result

    def mark_sent(
        self, *, organization_id: str, notification_id: str, actor_id: str
    ) -> Notification:
        notification = self._get(
            organization_id=organization_id, notification_id=notification_id
        )
        if notification.status != "PENDING":
            raise ValueError("only pending notifications can be marked sent")
        notification.status = "SENT"
        notification.sent_by = actor_id
        notification.sent_at = utc_now().isoformat()
        self._save(notification)
        self._audit(
            organization_id,
            actor_id,
            "ESCALATION_NOTIFICATION_MARKED_SENT",
            f"case:{notification.case_id}",
            notification_id=notification_id,
        )
        return notification

    def _get(self, *, organization_id: str, notification_id: str) -> Notification:
        notification = self.store.notifications.get((organization_id, notification_id))
        if notification is None and self._has_repository_method("get_notification"):
            row = self.repository.get_notification(organization_id, notification_id)
            if row:
                notification = Notification(**row)
                self.store.notifications[(organization_id, notification_id)] = (
                    notification
                )
        if notification is None:
            raise KeyError("notification not found")
        return notification

    def _load_notifications(self, organization_id: str, *, status: str | None) -> None:
        if self._has_repository_method("list_notifications"):
            for row in self.repository.list_notifications(organization_id, status):
                notification = Notification(**row)
                self.store.notifications[
                    (organization_id, notification.notification_id)
                ] = notification

    def _save(self, notification: Notification) -> None:
        if self._has_repository_method("update_notification"):
            self.repository.update_notification(
                notification.organization_id, notification.payload()
            )

    def _has_repository_method(self, name: str) -> bool:
        return self.repository is not None and hasattr(self.repository, name)

    def _audit(
        self,
        organization_id: str,
        actor_id: str,
        event: str,
        subject: str,
        **details: Any,
    ) -> None:
        if self.audit_event:
            self.audit_event(organization_id, actor_id, event, subject, **details)
