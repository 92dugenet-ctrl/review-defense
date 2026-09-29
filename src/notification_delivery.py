"""V6.12 controlled notification delivery.

Delivery is explicit and operator-triggered. It performs no Google resource mutation.
Webhook targets are validated against SSRF/private-network protections; email uses
configured SMTP only. Tests can inject transports so no network is required.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
import smtplib
import socket
from email.message import EmailMessage
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_WEBHOOK_SCHEMES = {"https"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "::1", "metadata.google.internal"}

class DeliveryError(Exception):
    pass

@dataclass(frozen=True)
class DeliveryResult:
    channel: str
    delivered: bool
    provider: str
    detail: str


def validate_webhook_target(target: str, *, resolver=socket.getaddrinfo) -> str:
    p = urlparse(target.strip())
    if p.scheme not in ALLOWED_WEBHOOK_SCHEMES or not p.hostname or p.username or p.password:
        raise DeliveryError("webhook target must be an https URL without credentials")
    host = p.hostname.lower().rstrip(".")
    if host in BLOCKED_HOSTS or host.endswith(".google.internal"):
        raise DeliveryError("webhook target is not allowed")
    try:
        infos = resolver(host, p.port or 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise DeliveryError("webhook hostname cannot be resolved") from exc
    for info in infos:
        addr = info[4][0]
        ip = ipaddress.ip_address(addr)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise DeliveryError("webhook target resolves to a non-public address")
    return target.strip()


def deliver_webhook(notification, *, opener=urlopen, timeout=8, resolver=socket.getaddrinfo) -> DeliveryResult:
    target = validate_webhook_target(notification.target, resolver=resolver)
    payload = ("{\"notification_id\":\"%s\",\"case_id\":\"%s\",\"level\":\"%s\",\"subject\":%s,\"body\":%s}" % (
        notification.notification_id, notification.case_id, notification.escalation_level,
        __import__('json').dumps(notification.subject), __import__('json').dumps(notification.body))).encode()
    req = Request(target, data=payload, method="POST", headers={"Content-Type":"application/json", "User-Agent":"ReviewDefense/6.12"})
    with opener(req, timeout=timeout) as response:
        if not (200 <= getattr(response, "status", 200) < 300):
            raise DeliveryError(f"webhook returned HTTP {getattr(response, 'status', 'unknown')}")
    return DeliveryResult("WEBHOOK", True, "https-webhook", "delivered")


def deliver_email(notification, *, host: str, port: int = 587, username: str | None = None,
                  password: str | None = None, sender: str | None = None, starttls: bool = True,
                  smtp_factory=smtplib.SMTP, timeout=10) -> DeliveryResult:
    if not host or not sender:
        raise DeliveryError("SMTP host and sender are required")
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = notification.target
    msg["Subject"] = notification.subject
    msg.set_content(notification.body)
    with smtp_factory(host, port, timeout=timeout) as smtp:
        if starttls:
            smtp.starttls()
        if username:
            smtp.login(username, password or "")
        smtp.send_message(msg)
    return DeliveryResult("EMAIL", True, "smtp", "delivered")


def deliver(notification, *, email_config=None, opener=urlopen, smtp_factory=smtplib.SMTP, resolver=socket.getaddrinfo) -> DeliveryResult:
    if notification.status != "PENDING":
        raise DeliveryError("only pending notifications can be delivered")
    if notification.channel == "IN_APP":
        return DeliveryResult("IN_APP", True, "internal", "acknowledged for in-app delivery")
    if notification.channel == "WEBHOOK":
        return deliver_webhook(notification, opener=opener, resolver=resolver)
    if notification.channel == "EMAIL":
        cfg = email_config or {}
        return deliver_email(notification, smtp_factory=smtp_factory, **cfg)
    raise DeliveryError("unsupported notification channel")
