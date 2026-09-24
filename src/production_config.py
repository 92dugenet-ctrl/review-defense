"""V6.20 production configuration and startup validation."""
from __future__ import annotations
import os
from dataclasses import dataclass

TRUTHY = {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class ProductionConfig:
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8080
    database_dsn: str | None = None
    trust_proxy: bool = False
    secure_headers: bool = True
    max_request_bytes: int = 1_000_000
    evidence_max_request_bytes: int = 35_000_000
    recovery_email_enabled: bool = False
    require_email_verification: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender: str | None = None
    smtp_starttls: bool = True
    public_base_url: str = "http://localhost:8080"
    evidence_storage_root: str = "/var/lib/review-defense/evidence"

    @classmethod
    def from_env(cls) -> "ProductionConfig":
        configured_env = os.getenv("REVIEW_DEFENSE_ENV", "").strip().lower()
        public_base_url = os.getenv("REVIEW_DEFENSE_PUBLIC_BASE_URL", "http://localhost:8080").rstrip("/")
        env = configured_env or (
            "production" if public_base_url.startswith("https://") else "development"
        )
        port = int(os.getenv("PORT", "8080"))
        if not 1 <= port <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        max_request = int(os.getenv("MAX_REQUEST_BYTES", "1000000"))
        evidence_max = int(os.getenv("EVIDENCE_MAX_REQUEST_BYTES", "35000000"))
        recovery_email_enabled = os.getenv("REVIEW_DEFENSE_RECOVERY_EMAIL_ENABLED", "false").lower() in TRUTHY
        require_email_verification = os.getenv("REVIEW_DEFENSE_REQUIRE_EMAIL_VERIFICATION", "false").lower() in TRUTHY
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        if max_request <= 0 or evidence_max <= 0:
            raise ValueError("request limits must be positive")
        return cls(
            environment=env,
            host=os.getenv("HOST", "127.0.0.1"),
            port=port,
            database_dsn=os.getenv("DATABASE_URL") or os.getenv("REVIEW_DEFENSE_DATABASE_URL"),
            trust_proxy=os.getenv("TRUST_PROXY", "false").lower() in TRUTHY,
            secure_headers=os.getenv("SECURE_HEADERS", "true").lower() in TRUTHY,
            max_request_bytes=max_request,
            evidence_max_request_bytes=evidence_max,
            recovery_email_enabled=recovery_email_enabled,
            require_email_verification=require_email_verification,
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=smtp_port,
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            smtp_sender=os.getenv("SMTP_SENDER"),
            smtp_starttls=os.getenv("SMTP_STARTTLS", "true").lower() in TRUTHY,
            public_base_url=public_base_url,
            evidence_storage_root=os.getenv("EVIDENCE_STORAGE_ROOT", "/var/lib/review-defense/evidence"),
        )

    @property
    def production(self) -> bool:
        return self.environment in {"production", "prod"}

    def validate_startup(self, *, require_database: bool | None = None) -> None:
        if self.production and not self.database_dsn and (require_database is not False):
            raise ValueError("DATABASE_URL is required in production")
        if self.production and self.host in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("production server must bind to a non-loopback host")
        if self.recovery_email_enabled or self.require_email_verification:
            if not self.smtp_host or not self.smtp_sender:
                raise ValueError("SMTP_HOST and SMTP_SENDER are required when authentication email is enabled")
            if self.production and not self.public_base_url.startswith("https://"):
                raise ValueError("production authentication email links require an HTTPS public base URL")
