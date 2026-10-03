"""V6.25 transactional authentication emails.

Recovery/verification emails are explicit SMTP sends. No Google mutation is
performed and tokens are never persisted in clear text.
"""

# Adaptateur SMTP dédié aux emails de vérification et de récupération. Il construit les liens et transmet le message ; la génération, le hash, l'expiration et la consommation des tokens restent gérés par les composants d'identité et leur repository.

from __future__ import annotations

# Architecture : adaptateur d'envoi SMTP pour les messages de récupération et de vérification d'adresse.
# Les services d'identité construisent le contexte et les liens à envoyer ; ce module assure uniquement
# le transport du message vers le serveur SMTP configuré par l'environnement.
# Les identifiants SMTP et les paramètres de connexion sont des secrets/configurations serveur :
# ils ne doivent jamais être exposés au navigateur ni enregistrés dans les journaux applicatifs.
# Un succès SMTP confirme la remise au serveur de courrier, pas la lecture par le destinataire.

from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import quote
import smtplib

class RecoveryEmailError(Exception):
    pass

@dataclass(frozen=True)
class SMTPConfig:
    host: str
    port: int = 587
    username: str | None = None
    password: str | None = None
    sender: str = ""
    starttls: bool = True
    timeout: int = 10


def build_recovery_link(base_url: str, organization_id: str, token: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/reset-password?organization_id={quote(organization_id)}&token={quote(token)}"


def build_verification_link(base_url: str, organization_id: str, token: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/verify-email?organization_id={quote(organization_id)}&token={quote(token)}"


def _send(*, recipient: str, subject: str, body: str, config: SMTPConfig, smtp_factory=smtplib.SMTP) -> None:
    if not config.host or not config.sender:
        raise RecoveryEmailError("SMTP host and sender are required")
    if config.username and not config.starttls:
        raise RecoveryEmailError(
            "SMTP authentication requires STARTTLS on this transport"
        )
    msg = EmailMessage()
    msg["From"] = config.sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtp_factory(config.host, config.port, timeout=config.timeout) as smtp:
            if config.starttls:
                smtp.starttls()
            if config.username:
                smtp.login(config.username, config.password or "")
            smtp.send_message(msg)
    except Exception as exc:
        raise RecoveryEmailError("authentication email delivery failed") from exc


def send_recovery_email(*, recipient: str, organization_id: str, token: str, base_url: str, config: SMTPConfig, smtp_factory=smtplib.SMTP) -> None:
    link = build_recovery_link(base_url, organization_id, token)
    body = (
        "A password reset was requested for your Review Defense account.\n\n"
        f"Reset your password here: {link}\n\n"
        "This link expires after 30 minutes and can only be used once.\n"
        "If you did not request this, you can safely ignore this message.\n"
    )
    _send(recipient=recipient, subject="Review Defense — Password reset", body=body, config=config, smtp_factory=smtp_factory)


def send_verification_email(*, recipient: str, organization_id: str, token: str, base_url: str, config: SMTPConfig, smtp_factory=smtplib.SMTP) -> None:
    link = build_verification_link(base_url, organization_id, token)
    body = (
        "Verify your Review Defense email address.\n\n"
        f"Verify your email here: {link}\n\n"
        "This link expires after 24 hours and can only be used once.\n"
    )
    _send(recipient=recipient, subject="Review Defense — Verify your email", body=body, config=config, smtp_factory=smtp_factory)
