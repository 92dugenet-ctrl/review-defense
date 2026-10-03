"""Contrats de déploiement et de sécurité HTTP.

DeploymentConfig décrit l'adresse publique et la relation avec le reverse proxy.
validate() est appelé par le contrôle pré-démarrage et par la composition API
en production. security_headers() fournit les en-têtes que les réponses HTTP
peuvent appliquer ; ce module ne configure pas lui-même Caddy ou Gunicorn.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DeploymentConfig:
    """Paramètres de déploiement immuables chargés depuis l'environnement."""

    public_base_url: str
    environment: str
    trust_proxy: bool

    @classmethod
    def from_env(cls) -> "DeploymentConfig":
        """Construit le contrat de déploiement à partir des variables runtime."""
        public_base_url = os.getenv(
            "REVIEW_DEFENSE_PUBLIC_BASE_URL",
            "http://localhost:8080",
        ).strip().rstrip("/")
        configured_environment = os.getenv(
            "REVIEW_DEFENSE_ENV",
            "",
        ).strip().lower()
        # Keep environment inference identical to ProductionConfig: HTTPS is
        # treated as production when no explicit environment is supplied.
        environment = configured_environment or (
            "production"
            if public_base_url.startswith("https://")
            else "development"
        )

        return cls(
            public_base_url=public_base_url,
            environment=environment,
            trust_proxy=os.getenv("TRUST_PROXY", "false").strip().lower()
            in {"1", "true", "yes", "on"},
        )

    @property
    def production(self) -> bool:
        """Indique si les contrôles stricts de production doivent être appliqués."""
        return self.environment in {"production", "prod"}

    def validate(self) -> None:
        """Refuse les combinaisons de production incompatibles avec un proxy TLS."""
        if self.production and not self.public_base_url.startswith("https://"):
            raise ValueError("production public base URL must use HTTPS")

        if self.production and self.trust_proxy is False:
            # Un proxy TLS termine HTTPS avant WSGI ; ses en-têtes ne sont fiables
            # que si ce déploiement l'a explicitement déclaré comme proxy de confiance.
            raise ValueError("TRUST_PROXY=true is required when production runs behind a trusted reverse proxy")


# Politique CSP centralisée pour limiter les origines autorisées par le navigateur.
CSP = (
    "default-src 'self'; "
    "base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; "
    "script-src 'self' 'unsafe-inline' https://www.paypal.com https://www.paypalobjects.com; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self' data:; connect-src 'self' https://www.paypal.com https://api-m.paypal.com; frame-src 'self' https://www.paypal.com https://www.sandbox.paypal.com; "
    "media-src 'none'; worker-src 'none'; manifest-src 'self'"
)

# Candidate policy without inline execution; kept in report-only during migration.
CSP_REPORT_ONLY = (
    "default-src 'self'; base-uri 'self'; object-src 'none'; "
    "frame-ancestors 'none'; form-action 'self'; "
    "script-src 'self' https://www.paypal.com https://www.paypalobjects.com; "
    "script-src-attr 'none'; style-src 'self'; style-src-attr 'none'; "
    "img-src 'self' data:; font-src 'self' data:; "
    "connect-src 'self' https://www.paypal.com https://api-m.paypal.com; "
    "frame-src 'self' https://www.paypal.com https://www.sandbox.paypal.com; "
    "media-src 'none'; worker-src 'none'; manifest-src 'self'"
)


def security_headers(*, production: bool) -> dict[str, str]:
    """Retourne les en-têtes de défense en profondeur à appliquer aux réponses."""
    headers = {
        "Content-Security-Policy": CSP,
        "Content-Security-Policy-Report-Only": CSP_REPORT_ONLY,
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
    }

    if production:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return headers
