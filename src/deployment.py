"""V6.27 production deployment/security contracts."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DeploymentConfig:
    public_base_url: str
    environment: str
    trust_proxy: bool

    @classmethod
    def from_env(cls) -> "DeploymentConfig":
        return cls(
            public_base_url=os.getenv("REVIEW_DEFENSE_PUBLIC_BASE_URL", "http://localhost:8080").rstrip("/"),
            environment=os.getenv("REVIEW_DEFENSE_ENV", "development").lower(),
            trust_proxy=os.getenv("TRUST_PROXY", "false").lower() in {"1", "true", "yes", "on"},
        )

    @property
    def production(self) -> bool:
        return self.environment in {"production", "prod"}

    def validate(self) -> None:
        if self.production and not self.public_base_url.startswith("https://"):
            raise ValueError("production public base URL must use HTTPS")
        if self.production and self.trust_proxy is False:
            # A public TLS reverse proxy normally terminates TLS before WSGI.
            # Requiring explicit opt-in prevents trusting spoofable forwarded headers.
            raise ValueError("TRUST_PROXY=true is required when production runs behind a trusted reverse proxy")


CSP = (
    "default-src 'self'; "
    "base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; "
    "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; "
    "media-src 'none'; worker-src 'none'; manifest-src 'self'"
)


def security_headers(*, production: bool) -> dict[str, str]:
    headers = {
        "Content-Security-Policy": CSP,
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
