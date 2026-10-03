"""Application HTTP/API utilisée par le point d'entrée WSGI de production.

wsgi.py importe create_app() depuis ce module et expose l'objet obtenu sous
wsgi:app à Gunicorn. Cette classe WSGI centralise le routage métier /v1, la
session, les permissions, les limites de requête et la conversion des erreurs.

Les services spécialisés exécutent les règles métier ; repository délègue la
persistance PostgreSQL. MemoryStore conserve un cache et un mode local, mais
ne remplace pas le stockage partagé requis en production.
"""
from __future__ import annotations

import os
import re

import base64
import hmac
import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass
from http.cookies import SimpleCookie
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs, urlsplit

from .evidence_vault import FilesystemObjectStore, InMemoryObjectStore, sign_download_url, verify_integrity
from .security_hardening import (
    RateLimiter,
    Session,
    generate_session_token,
    hash_password,
    verify_password,
    utc_now,
    hash_token,
    validate_upload,
    MAX_UPLOAD_BYTES,
)
from .app_shell import SessionContext, can_access
from .case_service import Case, CaseService
from .case_lifecycle_service import CaseLifecycleService
from .case_workspace_service import CaseWorkspaceService
from .case_decision_service import CaseDecisionService
from .case_submission_service import CaseSubmissionService
from .case_approval_service import CaseApprovalService
from .case_evidence_matrix_service import CaseEvidenceMatrixService
from .case_operations_service import CaseOperationsService
from .case_escalation_service import CaseEscalationService
from .review_workspace import ReviewContext, extract_claims, classify_policy_signals
from .contradiction_engine import EvidenceFact, detect_contradictions
from .evidence_extraction import extract_text_fact_suggestions
from .evidence_ocr import extract_readable_text, ExtractionError
from .review_queue import score_case, sort_queue
from .case_sla_service import CaseSLAService
from .business_calendar import calendar_from_dict, default_calendar
from .escalation_workflow import Escalation, signal_from_sla
from .notification_outbox import Notification
from .notification_service import NotificationService
from .notification_delivery import deliver, DeliveryError
from .notification_worker import NotificationWorker
from .notification_policy import NotificationPolicy, validate_policy, evaluate
from .notification_observability import build_notification_metrics
from .case_review import ReviewChecklistItem, build_checklist, assess_readiness
from .case_review_service import CaseReviewService
from .case_contradiction_service import CaseContradictionService
from .case_review_matrix import build_evidence_matrix
from .operations_ui import (
    ReviewSummary, ClaimView, PolicySignalView, EvidenceView, TimelineEvent,
    Contradiction, CaseWorkspace, missing_evidence_tasks, case_requires_human_review,
)
from .identity import normalize_email, validate_role, issue_session, can_manage_org
from .production_config import ProductionConfig
from .mfa import (
    generate_secret,
    verify_totp,
    totp_code,
    otpauth_uri,
    encrypt_secret,
    decrypt_secret,
    recovery_token,
)
from .recovery_email import SMTPConfig, send_recovery_email, send_verification_email, RecoveryEmailError
from .deployment import DeploymentConfig, security_headers
from .observability import InMemoryTelemetry, TraceContext, health_check
from .seo_renderer import is_seo_path, render_page, sitemap, robots
from .billing_catalog import PAYPAL_SUBSCRIPTION_CLIENT_ID, get_offer, paypal_plan_id, public_catalog
from .google_business_profile import (
    OAuthStateManager,
    GoogleOAuthClient,
    GoogleBusinessProfileClient,
    GoogleAPIError,
    GoogleIntegrationError,
)
from .billing_service import account_status, plan_for_offer, public_plans
from .paypal_client import (
    configured as paypal_configured,
    configuration_status as paypal_configuration_status,
    verify_webhook as paypal_verify_webhook,
    request_json as paypal_request_json,
    access_token as paypal_access_token,
    PayPalError,
)


class APIError(Exception):
    """Erreur HTTP contrôlée convertie en réponse JSON par __call__.

    status devient le statut HTTP ; code et message forment le contrat
    d'erreur consommé par le client frontend ; details apporte un contexte
    structuré facultatif sans exposer les exceptions internes.
    """

    def __init__(self, status: int, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


@dataclass(frozen=True)
class User:
    """Identité résolue après authentification et liée à un tenant.

    organization_id limite les données accessibles ; role porte les droits.
    password_hash est une donnée interne qui ne doit jamais être renvoyée.
    """

    user_id: str
    organization_id: str
    email: str
    password_hash: str
    role: str



class MemoryStore:
    """Cache local des objets métier et état du mode sans PostgreSQL.

    En production, repository porte les données partagées entre workers.
    Les pièces jointes passent par un ObjectStore distinct du cache mémoire.
    """

    def __init__(self) -> None:
        """Initialise les collections métier et le stockage des pièces jointes."""
        self.users: dict[str, User] = {}
        self.sessions: dict[str, Session] = {}
        self.reviews: dict[tuple[str, str], ReviewContext] = {}
        self.cases: dict[tuple[str, str], Case] = {}
        self.decisions: dict[tuple[str, str], Any] = {}
        self.snapshots: dict[tuple[str, str], Any] = {}
        self.approvals: list[Any] = []
        self.submissions: dict[tuple[str, str], dict[str, Any]] = {}
        self.idempotency: dict[tuple[str, str], tuple[str, Any]] = {}
        self.audit: list[dict[str, Any]] = []
        evidence_root = os.environ.get("REVIEW_DEFENSE_EVIDENCE_ROOT", "").strip()
        # Production runs with multiple Gunicorn workers. A process-local in-memory
        # vault makes evidence uploaded by one worker invisible to another worker.
        # Use a shared filesystem vault in production; deployments can override the
        # path with REVIEW_DEFENSE_EVIDENCE_ROOT on persistent storage.
        if evidence_root:
            self.vault = FilesystemObjectStore(evidence_root)
        elif os.environ.get("REVIEW_DEFENSE_ENV", "").strip().lower() in {"production", "prod"}:
            # Production uploads must live on a mounted persistent volume, not /tmp.
            self.vault = FilesystemObjectStore("/var/lib/review-defense/evidence")
        else:
            self.vault = InMemoryObjectStore()
        self.evidence: dict[tuple[str, str], dict[str, Any]] = {}
        self.evidence_facts: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.contradictions: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.fact_suggestions: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.case_assignments: dict[tuple[str, str], str | None] = {}
        self.download_secret = secrets.token_bytes(32)
        self.invitations: dict[str, dict[str, Any]] = {}
        self.sla_calendars: dict[str, dict[str, Any]] = {}
        self.escalations: dict[tuple[str, str, str], Escalation] = {}
        self.notifications: dict[tuple[str, str], Notification] = {}
        self.notification_policies: dict[str, NotificationPolicy] = {}
        self.review_checklists: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.contradiction_dispositions: dict[tuple[str, str], dict[str, Any]] = {}
        self.contradiction_disposition_history: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self.mfa: dict[str, dict[str, Any]] = {}
        self.recovery_tokens: dict[str, dict[str, Any]] = {}
        self.email_verification_tokens: dict[str, dict[str, Any]] = {}
        self.privacy_requests: dict[str, dict[str, Any]] = {}
        self.privacy_consents: list[dict[str, Any]] = []
        self.email_verified: dict[str, bool] = {}
        self.billing: dict[str, dict[str, Any]] = {}
        self.billing_accounts: dict[str, dict[str, Any]] = {}
        self.billing_events: list[dict[str, Any]] = []
        self.organization_profiles: dict[str, dict[str, Any]] = {}
        self.client_documents: dict[tuple[str, str], dict[str, Any]] = {}
        self.google_oauth_states: dict[str, dict[str, Any]] = {}
        self.google_connections: dict[tuple[str, str], dict[str, Any]] = {}

    def audit_event(self, org: str, actor: str | None, action: str, resource: str, **meta: Any) -> None:
        """Ajoute un événement d'audit associé à une organisation et un acteur."""
        self.audit.append({
            "event_id": str(uuid.uuid4()), "organization_id": org, "actor_id": actor,
            "action": action, "resource": resource, "at": utc_now().isoformat(), "meta": meta,
        })


def _iso_value(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _review_from_row(row: Any) -> ReviewContext:
    """Convert a persistent api_reviews row into the API review contract."""
    return ReviewContext(
        review_id=str(row[0]),
        organization_id=str(row[1]),
        location_id=str(row[2] or ""),
        author_display_name=row[3],
        rating=int(row[4]),
        text=str(row[5]),
        published_at=_iso_value(row[6]) or "",
        updated_at=_iso_value(row[7]),
        language=row[8],
        source=str(row[9] or "GOOGLE"),
        review_url=row[10],
    )


class ReviewDefenseAPI:
    """Application WSGI qui transforme environ en réponses HTTP.

    handle() porte le routage et les règles d'endpoint. Les méthodes privées
    partagent les contrôles transverses (authentification, JSON, rôles,
    idempotence). Les services injectés réalisent les opérations métier.
    __call__() adapte les réponses au protocole WSGI.
    """

    def __init__(
        self,
        store: MemoryStore | None = None,
        *,
        session_ttl: int = 3600,
        limiter: RateLimiter | None = None,
        repository=None,
        delivery_email_config: dict[str, Any] | None = None,
        delivery_func=deliver,
        config: ProductionConfig | None = None,
    ):
        """Assemble les dépendances transverses et les services métier.

        store porte l'état local ; repository est l'adaptateur PostgreSQL.
        Les services reçoivent les deux pour gérer mode local et production.
        """
        self.store = store or MemoryStore()
        self.config = config or ProductionConfig.from_env()
        self.config.validate_startup(require_database=(repository is not None or self.config.production))
        self.repository = repository
        self.delivery_email_config = delivery_email_config or {}
        if not self.delivery_email_config and self.config.smtp_host and self.config.smtp_sender:
            self.delivery_email_config = {
                "host": self.config.smtp_host,
                "port": self.config.smtp_port,
                "username": self.config.smtp_username,
                "password": self.config.smtp_password,
                "sender": self.config.smtp_sender,
                "starttls": self.config.smtp_starttls,
            }
        self.delivery_func = delivery_func
        self.notification_worker = NotificationWorker(
            delivery_func=delivery_func,
            email_config=self.delivery_email_config,
        )
        self.notifications = NotificationService(
            store=self.store,
            repository=self.repository,
            audit_event=self.store.audit_event,
            delivery_func=self.delivery_func,
            email_config=self.delivery_email_config,
            policy_provider=self._notification_policy,
            worker=self.notification_worker,
        )
        self.session_ttl = session_ttl
        self.limiter = limiter or RateLimiter(limit=120, window_seconds=60)
        self.auth_limiter = RateLimiter(limit=8, window_seconds=300)
        self.recovery_limiter = RateLimiter(limit=5, window_seconds=3600)
        self.billing_accounts = self.store.billing_accounts
        self.billing_events = self.store.billing_events
        self._idem_lock = __import__("threading").RLock()
        self.telemetry = InMemoryTelemetry()
        if self.config.production:
            DeploymentConfig(
                public_base_url=self.config.public_base_url,
                environment=self.config.environment,
                trust_proxy=self.config.trust_proxy,
            ).validate()
        self.store.sla_calendars = self.store.sla_calendars
        self.store.escalations = self.store.escalations
        self.store.notifications = self.store.notifications
        self.case_lifecycle = CaseLifecycleService(store=self.store, repository=self.repository, audit_event=self.store.audit_event)
        self.case_sla = CaseSLAService(repository=self.repository, audit_event=self.store.audit_event)
        self.case_review = CaseReviewService(store=self.store, repository=self.repository, audit_event=self.store.audit_event)
        self.case_contradictions = CaseContradictionService(
            repository=self.repository,
            audit_event=self.store.audit_event,
            contradiction_store=self.store.contradictions,
            disposition_store=self.store.contradiction_dispositions,
            disposition_history_store=self.store.contradiction_disposition_history,
        )
        self.case_decisions = CaseDecisionService(
            store=self.store,
            repository=self.repository,
            audit_event=self.store.audit_event,
        )
        self.case_submissions = CaseSubmissionService(
            store=self.store,
            repository=self.repository,
            audit_event=self.store.audit_event,
        )
        self.case_approvals = CaseApprovalService(store=self.store, repository=self.repository)
        self.case_evidence_matrix = CaseEvidenceMatrixService(store=self.store)
        self.case_operations = CaseOperationsService(store=self.store, repository=self.repository, audit_event=self.store.audit_event)
        self.case_escalations = CaseEscalationService(store=self.store, repository=self.repository, audit_event=self.store.audit_event)

    def _client_ip_hash(self, environ) -> str:
        import hashlib
        ip = environ.get("REMOTE_ADDR", "unknown") or "unknown"
        return hashlib.sha256(ip.encode()).hexdigest()

    def _user_agent(self, environ) -> str | None:
        value = environ.get("HTTP_USER_AGENT")
        return value[:512] if isinstance(value, str) else None

    def _auth_key(self, environ, email: str) -> str:
        return f"{environ.get('REMOTE_ADDR', 'unknown')}:{email}"

    def _allow_rate_limit(self, limiter: RateLimiter, key: str, scope: str) -> bool:
        """Use a shared atomic quota in PostgreSQL-backed deployments."""
        if self.repository is None or not hasattr(self.repository, "allow_rate_limit"):
            return limiter.allow(key)
        import hashlib

        key_hash = hashlib.sha256(f"{scope}:{key}".encode("utf-8")).hexdigest()
        try:
            return self.repository.allow_rate_limit(
                key_hash, limit=limiter.limit, window_seconds=limiter.window_seconds
            )
        except Exception as exc:
            raise APIError(
                503, "RATE_LIMIT_UNAVAILABLE",
                "shared rate limiting is temporarily unavailable",
            ) from exc

    def _persistent_uuid(self, value: Any, field: str) -> str:
        raw = str(value or "").strip()
        if self.repository is None or not getattr(self.repository, "uses_uuid_ids", False):
            return raw
        if not raw:
            raise APIError(422, "VALIDATION_ERROR", f"{field} is required")
        try:
            return str(uuid.UUID(raw))
        except (ValueError, TypeError, AttributeError) as exc:
            raise APIError(422, "VALIDATION_ERROR", f"{field} must be a valid UUID") from exc

    def _validate_persistent_resource_path(self, path: str) -> None:
        if self.repository is None or not getattr(self.repository, "uses_uuid_ids", False):
            return
        parts = path.split("/")
        if len(parts) >= 4 and parts[1:
            3] in (["v1", "cases"], ["v1", "evidence"], ["v1", "escalations"]):
            self._persistent_uuid(parts[3], "resource_id")
        elif len(parts) >= 4 and parts[1:
            3] == ["v1", "notifications"]:
            self._persistent_uuid(parts[3], "notification_id")
        elif len(parts) >= 5 and parts[1:
            4] == ["v1", "privacy", "requests"]:
            self._persistent_uuid(parts[4], "request_id")
        elif len(parts) >= 6 and parts[1:
            4] == ["v1", "organization", "members"] and parts[5] == "role":
            self._persistent_uuid(parts[4], "user_id")

    def _user_for_organization(self, organization_id: str, user_id: str) -> User | None:
        if self.repository is not None and hasattr(self.repository, "get_user_by_id"):
            row = self.repository.get_user_by_id(organization_id, user_id)
            if not row:
                return None
            user = User(str(row[0]), organization_id, str(row[1]), str(row[2]), str(row[3]))
            self.store.users[user.user_id] = user
            return user
        user = self.store.users.get(user_id)
        return user if user is not None and user.organization_id == organization_id else None

    def _calendar(self, organization_id: str):
        if organization_id not in self.store.sla_calendars and self.repository is not None and hasattr(self.repository, "get_sla_calendar"):
            row = self.repository.get_sla_calendar(organization_id)
            if row:
                self.store.sla_calendars[organization_id] = row
        return calendar_from_dict(self.store.sla_calendars.get(organization_id)) if organization_id in self.store.sla_calendars else default_calendar()

    def _notification_policy(self, organization_id: str):
        if organization_id not in self.store.notification_policies and self.repository is not None and hasattr(self.repository, "get_notification_policy"):
            row = self.repository.get_notification_policy(organization_id)
            if row:
                self.store.notification_policies[organization_id] = validate_policy(organization_id, row)
        return self.store.notification_policies.get(organization_id) or validate_policy(organization_id, {})

    def _escalation_for(self, organization_id: str, case_id: str, sla):
        return self.case_escalations.for_sla(
            organization_id=organization_id, case_id=case_id, sla=sla
        )

    def seed_user(self, *, organization_id: str, email: str, password: str, role: str = "OWNER") -> User:
        if role not in {"OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER"}:
            raise ValueError("invalid role")
        email = normalize_email(email)
        validate_role(role)
        user = User(str(uuid.uuid4()), organization_id, email, hash_password(password), role)
        if self.repository is not None:
            uid, _, _ph, _role = self.repository.create_user(organization_id, user.email, user.password_hash, role)
            user = User(uid, organization_id, user.email, user.password_hash, role)
        self.store.users[user.user_id] = user
        self.store.email_verified[user.user_id] = True
        if self.repository is not None and hasattr(self.repository, "mark_email_verified"):
            self.repository.mark_email_verified(organization_id, user.user_id)
        return user

    def _json(
        self,
        status: int,
        payload: Mapping[str, Any],
        headers: Mapping[str, str] | None = None,
    ):
        response_headers = {
            "Content-Type": "application/json; charset=utf-8",
            **(headers or {}),
        }
        response_payload = dict(payload)
        if self.config.cookie_auth_enabled and response_payload.get("access_token"):
            raw_token = str(response_payload.pop("access_token"))
            cookie_parts = [
                f"{self._session_cookie_name()}={raw_token}",
                "Path=/",
                f"Max-Age={self.session_ttl}",
                "HttpOnly",
                "SameSite=Lax",
            ]
            if self.config.production:
                cookie_parts.append("Secure")
            response_headers["Set-Cookie"] = "; ".join(cookie_parts)
            response_payload["csrf_token"] = self._csrf_token(raw_token)
        body = json.dumps(response_payload, ensure_ascii=False).encode()
        return status, response_headers, body

    def _privacy_request_payload(self, row: Any) -> dict[str, Any]:
        if isinstance(row, dict):
            return dict(row)
        keys = ("id","organization_id","requester_user_id","request_type","status","details","response_note","due_at","created_at","updated_at")
        return dict(zip(keys, row))

    def _privacy_export(self, user: User) -> dict[str, Any]:
        requests = []
        consents = []
        if self.repository is not None:
            if hasattr(self.repository, "list_privacy_requests"):
                requests = [self._privacy_request_payload(r) for r in (self.repository.list_privacy_requests(user.organization_id, user.user_id) or [])]
            if hasattr(self.repository, "list_privacy_consents"):
                rows = self.repository.list_privacy_consents(user.organization_id, user.user_id) or []
                consents = [dict(zip(("id","purpose","policy_version","granted","granted_at","withdrawn_at"), r)) for r in rows]
        if not requests:
            requests = [dict(v) for v in self.store.privacy_requests.values()
                         if v.get("organization_id") == user.organization_id and v.get("requester_user_id") == user.user_id]
        if not consents:
            consents = [dict(v) for v in self.store.privacy_consents
                        if v.get("organization_id") == user.organization_id and v.get("user_id") == user.user_id]
        audit = [dict(e) for e in self.store.audit
                 if e.get("organization_id") == user.organization_id and e.get("actor_id") == user.user_id]
        return {
            "export_version": "1.0",
            "generated_at": utc_now().isoformat(),
            "scope": "personal_account_data",
            "account": {
                "user_id": user.user_id,
                "organization_id": user.organization_id,
                "email": user.email,
                "role": user.role,
            },
            "privacy_requests": requests,
            "consents": consents,
            "audit_events": audit,
            "note": (
            "This export covers personal account and privacy-request data available through this endpoint; organi" +
            "zation-owned business data remains subject to the applicable controller/processor relationship."
        )
        }

    def _session_cookie_name(self) -> str:
        return "__Host-review-defense-session" if self.config.production else "review-defense-session"

    def _cookie_session_token(self, environ) -> str | None:
        if not self.config.cookie_auth_enabled:
            return None
        parsed = SimpleCookie()
        try:
            parsed.load(environ.get("HTTP_COOKIE", ""))
        except Exception:
            return None
        for name in ("__Host-review-defense-session", "review-defense-session"):
            morsel = parsed.get(name)
            if morsel and morsel.value:
                return morsel.value
        return None

    @staticmethod
    def _csrf_token(raw_token: str) -> str:
        return hmac.new(
            raw_token.encode("utf-8"),
            b"review-defense-browser-csrf-v1",
            "sha256",
        ).hexdigest()

    def _auth(self, environ) -> User:
        """Valide le Bearer ou le cookie HttpOnly, puis la session et le rôle.

        Les mutations authentifiées par cookie sont protégées par handle().
        Le repository reste autoritaire pour la révocation et le rôle.
        """
        header = environ.get("HTTP_AUTHORIZATION", "")
        if isinstance(header, str) and header.startswith("Bearer "):
            raw = header[7:].strip()
        else:
            raw = self._cookie_session_token(environ) or ""
            if not raw:
                raise APIError(401, "AUTH_REQUIRED", "authentication required")
        if not raw or len(raw) > 4096:
            raise APIError(401, "AUTH_INVALID", "invalid or expired session")
        try:
            token_hash = hash_token(raw)
        except ValueError as exc:
            raise APIError(401, "AUTH_INVALID", "invalid or expired session") from exc
        session = self.store.sessions.get(token_hash)
        if session is None and self.repository is not None:
            # Resolve the opaque token through the narrowly scoped lookup function
            # when this worker has not seen the session yet.
            row = None
            if hasattr(self.repository, "get_session_by_token_hash"):
                row = self.repository.get_session_by_token_hash(token_hash)
            if row:
                _, uid, org, role, expires_at, revoked_at = row
                from datetime import datetime
                def parse(v):
                    if isinstance(v, datetime):
                        return v
                    return datetime.fromisoformat(str(v).replace('Z','+00:00'))
                session = Session(str(uid), str(org), str(role), token_hash, parse(expires_at), parse(revoked_at) if revoked_at else None)
                self.store.sessions[token_hash] = session
        # Do not trust a process-local session cache for revocation state. Another
        # Gunicorn worker may have revoked this token since it was cached here.
        if session is not None and self.repository is not None and hasattr(self.repository, "get_session"):
            row = self.repository.get_session(session.organization_id, token_hash)
            if not row:
                self.store.sessions.pop(token_hash, None)
                session = None
            else:
                _, uid, org, role, expires_at, revoked_at = row
                from datetime import datetime
                def parse(v):
                    if isinstance(v, datetime):
                        return v
                    return datetime.fromisoformat(str(v).replace('Z', '+00:00'))
                session = Session(str(uid), str(org), str(role), token_hash, parse(expires_at), parse(revoked_at) if revoked_at else None)
                self.store.sessions[token_hash] = session
        if session is None or not session.active():
            raise APIError(401, "AUTH_INVALID", "invalid or expired session")
        # Always refresh the effective role from the persistent membership source.
        # A cached session must not retain elevated permissions after a role change.
        if self.repository is not None and hasattr(self.repository, "get_user_by_id"):
            row = self.repository.get_user_by_id(session.organization_id, session.user_id)
            if row:
                uid, email, password_hash, role = row
                user = User(str(uid), session.organization_id, str(email), str(password_hash), str(role))
                self.store.users[user.user_id] = user
            else:
                user = None
        else:
            user = self.store.users.get(session.user_id)
        if user is None or user.organization_id != session.organization_id:
            raise APIError(401, "AUTH_INVALID", "invalid session")
        if self.repository is not None and hasattr(self.repository, "touch_session"):
            try:
                self.repository.touch_session(user.organization_id, token_hash, self._user_agent(environ), self._client_ip_hash(environ))
            except Exception:
                # Observability metadata must never turn a valid request into a 500.
                pass
        return user

    def _body(self, environ) -> dict[str, Any]:
        """Lit un objet JSON dans la limite autorisée pour la route courante."""
        try:
            path = environ.get("PATH_INFO", "")
            limit = self.config.evidence_max_request_bytes if path.startswith(("/v1/evidence", "/v1/client/documents")) else self.config.max_request_bytes
            length_raw = environ.get("CONTENT_LENGTH")
            length = int(length_raw) if length_raw else 0
            if length < 0 or length > limit:
                raise APIError(413, "PAYLOAD_TOO_LARGE", "request body too large")
            if environ.get("wsgi.input_terminated"):
                raw = environ["wsgi.input"].read(limit + 1)
                if len(raw) > limit:
                    raise APIError(413, "PAYLOAD_TOO_LARGE", "request body too large")
            else:
                raw = environ["wsgi.input"].read(length) if length else b"{}"
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict):
                raise ValueError
            return obj
        except APIError:
            raise
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise APIError(400, "INVALID_JSON", "request body must be a JSON object") from exc

    def _idem(self, user: User, environ, body: Mapping[str, Any], producer: Callable[[], Any]):
        """Protège une mutation contre les répétitions réseau.

        La clé est limitée à l'organisation et liée à l'empreinte du JSON.
        La même clé avec un autre payload produit un conflit HTTP 409.
        """
        key = environ.get("HTTP_IDEMPOTENCY_KEY")
        if not key:
            return producer()
        if len(key) > 200:
            raise APIError(400, "INVALID_IDEMPOTENCY_KEY", "idempotency key is too long")
        fp = __import__("hashlib").sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        k = (user.organization_id, key)
        with self._idem_lock:
            old = self.store.idempotency.get(k)
            if old:
                if old[0] != fp:
                    raise APIError(409, "IDEMPOTENCY_CONFLICT", "idempotency key reused with different payload")
                return old[1]
            result = producer()
            self.store.idempotency[k] = (fp, result)
            return result

    def _require_role(self, user: User, *roles: str):
        """Refuse une action si le rôle n'est pas dans la liste autorisée."""
        if user.role not in roles:
            raise APIError(403, "FORBIDDEN", "role is not permitted for this operation")

    def _mfa_key(self) -> str:
        import os
        key = os.getenv("REVIEW_DEFENSE_MFA_ENCRYPTION_KEY", "")
        if not key:
            if self.config.production:
                raise APIError(503, "MFA_NOT_CONFIGURED", "MFA encryption key is not configured")
            key = os.getenv("REVIEW_DEFENSE_DEV_MFA_KEY") or __import__("cryptography.fernet", fromlist=["Fernet"]).Fernet.generate_key().decode()
        return key

    def _mfa_state(self, user: User) -> dict[str, Any]:
        state = self.store.mfa.get(user.user_id)
        if state is not None:
            return state
        if self.repository is not None and hasattr(self.repository, "get_mfa_state"):
            row = self.repository.get_mfa_state(user.organization_id, user.user_id)
            if row:
                state = {"enabled": bool(row[0]), "secret_enc": row[1], "last_counter": row[2] if len(row) > 2 else None}
                self.store.mfa[user.user_id] = state
                return state
        return {"enabled": False, "secret_enc": None, "last_counter": None}

    def _mfa_secret(self, user: User) -> str | None:
        state = self._mfa_state(user)
        if not state.get("enabled") or not state.get("secret_enc"):
            return None
        return decrypt_secret(state["secret_enc"], self._mfa_key())

    def _consume_mfa_code(self, user: User, code: str) -> bool:
        secret = self._mfa_secret(user)
        if secret is None:
            return True
        if not verify_totp(secret, code):
            return False
        counter = int(time.time() // 30)
        state = self._mfa_state(user)
        previous = state.get("last_counter")
        if previous is not None and counter <= int(previous):
            return False
        if self.repository is not None and hasattr(self.repository, "consume_mfa_counter"):
            if not self.repository.consume_mfa_counter(user.organization_id, user.user_id, counter):
                return False
        state["last_counter"] = counter
        self.store.mfa[user.user_id] = state
        return True

    def _smtp_config(self) -> SMTPConfig:
        cfg = self.delivery_email_config
        return SMTPConfig(host=str(cfg.get("host", "")), port=int(cfg.get("port", 587)),
                          username=cfg.get("username"), password=cfg.get("password"),
                          sender=str(cfg.get("sender", "")), starttls=bool(cfg.get("starttls", True)))

    def _email_verified(self, user: User) -> bool:
        if user.user_id in self.store.email_verified:
            return bool(self.store.email_verified[user.user_id])
        if self.repository is not None and hasattr(self.repository, "get_email_verified"):
            value = self.repository.get_email_verified(user.organization_id, user.user_id)
            self.store.email_verified[user.user_id] = bool(value)
            return bool(value)
        return False

    def _issue_email_verification(self, user: User) -> tuple[str, str]:
        raw, token_hash = recovery_token()
        from datetime import timedelta
        expires = utc_now() + timedelta(hours=24)
        row = {"organization_id": user.organization_id, "user_id": user.user_id,
               "token_hash": token_hash, "expires_at": expires.isoformat(), "used_at": None}
        self.store.email_verification_tokens[token_hash] = row
        if self.repository is not None and hasattr(self.repository, "create_email_verification_token"):
            self.repository.create_email_verification_token(user.organization_id, user.user_id, token_hash, expires.isoformat())
        return raw, expires.isoformat()

    def _metrics_response(self):
        lines = [
            "# HELP review_defense_requests_total Total HTTP requests.",
            "# TYPE review_defense_requests_total counter",
        ]
        for (name, labels), value in sorted(self.telemetry.counters.items()):
            if name != "http_requests_total":
                continue
            label_text = ",".join(f'{k}="{str(v).replace(chr(92), chr(92)+chr(92)).replace(chr(34), chr(92)+chr(34))}"' for k,v in labels)
            lines.append(f"http_requests_total{{{label_text}}} {value}")
        lines += [
            "# HELP review_defense_request_duration_ms Request duration summary.",
            "# TYPE review_defense_request_duration_ms gauge",
        ]
        for (name, labels), values in sorted(self.telemetry.timings.items()):
            if name != "http_request_duration_ms" or not values:
                continue
            label_text = ",".join(f'{k}="{str(v).replace(chr(92), chr(92)+chr(92)).replace(chr(34), chr(92)+chr(34))}"' for k,v in labels)
            lines.append(f"http_request_duration_ms{{{label_text},quantile=\"avg\"}} {sum(values)/len(values):.3f}")
            lines.append(f"http_request_duration_ms{{{label_text},quantile=\"max\"}} {max(values):.3f}")
        body = ("\\n".join(lines) + "\\n").encode()
        return 200, {"Content-Type": "text/plain; version=0.0.4; charset=utf-8"}, body

    def _google_secret(self) -> bytes:
        raw = os.getenv("REVIEW_DEFENSE_GOOGLE_TOKEN_KEY", "").strip()
        if raw:
            from cryptography.fernet import Fernet
            try:
                Fernet(raw.encode("ascii"))
                return raw.encode("ascii")
            except Exception as exc:
                raise APIError(503, "GOOGLE_TOKEN_KEY_INVALID", "Google token encryption key is invalid") from exc
        if self.config.production:
            raise APIError(503, "GOOGLE_INTEGRATION_NOT_CONFIGURED", "Google token encryption is not configured")
        if not hasattr(self, "_dev_google_key"):
            from cryptography.fernet import Fernet
            self._dev_google_key = Fernet.generate_key()
        return self._dev_google_key

    def _google_oauth(self):
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            raise APIError(503, "GOOGLE_INTEGRATION_NOT_CONFIGURED", "Google OAuth is not configured")
        state_secret = os.getenv("REVIEW_DEFENSE_GOOGLE_STATE_KEY", "").encode("utf-8")
        if not state_secret:
            if self.config.production:
                raise APIError(503, "GOOGLE_INTEGRATION_NOT_CONFIGURED", "Google OAuth state signing key is not configured")
            if not hasattr(self, "_dev_google_state_key"):
                self._dev_google_state_key = secrets.token_bytes(32)
            state_secret = self._dev_google_state_key
        if len(state_secret) < 32:
            raise APIError(503, "GOOGLE_STATE_KEY_INVALID", "Google OAuth state signing key must contain at least 32 bytes")
        return GoogleOAuthClient(client_id=client_id, client_secret=client_secret), OAuthStateManager(state_secret)

    def _google_connection(self, organization_id: str, connection_id: str) -> dict[str, Any] | None:
        if self.repository is not None and hasattr(self.repository, "get_google_connection"):
            row = self.repository.get_google_connection(organization_id, connection_id)
            if row:
                return {"connection_id": str(row[0]), "google_account_id": row[1], "google_location_id": row[2],
                        "location_title": row[3], "encrypted_access_token": row[4], "encrypted_refresh_token": row[5],
                        "expires_at": row[6], "status": row[7], "created_by": str(row[8]) if row[8] else None,
                        "updated_at": row[9]}
            return None
        return self.store.google_connections.get((organization_id, connection_id))

    def _google_connections(self, organization_id: str) -> list[dict[str, Any]]:
        if self.repository is not None and hasattr(self.repository, "list_google_connections"):
            rows = self.repository.list_google_connections(organization_id) or []
            return [{"connection_id": str(r[0]), "google_account_id": r[1], "google_location_id": r[2],
                     "location_title": r[3], "expires_at": _iso_value(r[4]), "status": r[5],
                     "created_by": str(r[6]) if r[6] else None, "updated_at": _iso_value(r[7])} for r in rows]
        return [dict(value) for (org, _), value in self.store.google_connections.items() if org == organization_id]

    def _google_access_token(self, organization_id: str, connection_id: str) -> tuple[str, dict[str, Any]]:
        from datetime import datetime, timedelta, timezone
        from cryptography.fernet import Fernet, InvalidToken
        connection = self._google_connection(organization_id, connection_id)
        if not connection or connection.get("status") != "CONNECTED":
            raise APIError(404, "GOOGLE_CONNECTION_NOT_FOUND", "Google connection not found")
        try:
            cipher = Fernet(self._google_secret())
            access_token = cipher.decrypt(str(connection["encrypted_access_token"]).encode()).decode()
            refresh_token = cipher.decrypt(str(connection["encrypted_refresh_token"]).encode()).decode() if connection.get("encrypted_refresh_token") else None
        except (InvalidToken, KeyError, ValueError) as exc:
            raise APIError(503, "GOOGLE_TOKEN_UNAVAILABLE", "Google connection token cannot be decrypted") from exc
        expires_raw = connection.get("expires_at")
        expires_at = expires_raw if isinstance(expires_raw, datetime) else datetime.fromisoformat(str(expires_raw).replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= utc_now() + timedelta(seconds=60):
            if not refresh_token:
                raise APIError(401, "GOOGLE_REAUTH_REQUIRED", "Google authorization has expired; reconnect the account")
            oauth_client, _ = self._google_oauth()
            try:
                refreshed = oauth_client.refresh(refresh_token)
            except (GoogleAPIError, GoogleIntegrationError) as exc:
                raise APIError(502, "GOOGLE_REFRESH_FAILED", "Google authorization could not be refreshed") from exc
            access_token = refreshed.access_token
            refresh_token = refreshed.refresh_token or refresh_token
            connection["encrypted_access_token"] = cipher.encrypt(access_token.encode()).decode()
            connection["encrypted_refresh_token"] = cipher.encrypt(refresh_token.encode()).decode() if refresh_token else None
            connection["expires_at"] = datetime.fromtimestamp(refreshed.expires_at, timezone.utc).isoformat()
            connection["updated_at"] = utc_now().isoformat()
            self.store.google_connections[(organization_id, connection_id)] = connection
            if self.repository is not None and hasattr(self.repository, "save_google_connection"):
                self.repository.save_google_connection(organization_id, connection)
        return access_token, connection

    def _client_profile(self, organization_id: str) -> dict[str, Any]:
        if self.repository is not None and hasattr(self.repository, "get_organization_profile"):
            row = self.repository.get_organization_profile(organization_id)
            if row:
                profile = dict(
                    zip(
                        (
                            "legal_name",
                            "website",
                            "phone",
                            "address",
                            "city",
                            "postal_code",
                            "country",
                            "sector",
                            "employee_count",
                            "description",
                            "updated_at",
                        ),
                        row,
                    )
                )
                self.store.organization_profiles[organization_id] = profile
                return profile
        return self.store.organization_profiles.get(organization_id, {})

    def _client_document_rows(self, organization_id: str) -> list[dict[str, Any]]:
        keys = ("document_id", "organization_id", "filename", "content_type", "size_bytes", "sha256", "object_key", "category", "created_by", "created_at")
        if self.repository is not None and hasattr(self.repository, "list_client_documents"):
            rows = self.repository.list_client_documents(organization_id) or []
            return [dict(zip(keys, row)) for row in rows]
        return [dict(value) for (org, _), value in self.store.client_documents.items() if org == organization_id]

    def _google_callback(self, environ):
        query = parse_qs(environ.get("QUERY_STRING", ""))
        code = str(query.get("code", [""])[0]).strip()
        state_value = str(query.get("state", [""])[0]).strip()
        error_value = str(query.get("error", [""])[0]).strip()
        if not state_value:
            raise APIError(400, "GOOGLE_OAUTH_INVALID", "Google OAuth state is missing")
        _, state_manager = self._google_oauth()
        try:
            state_manager.verify(state_value)
        except Exception as exc:
            raise APIError(400, "GOOGLE_OAUTH_STATE_INVALID", "Google OAuth state is invalid or expired") from exc
        state_row = None
        if self.repository is not None and hasattr(self.repository, "consume_google_oauth_state_by_state"):
            # PostgreSQL is authoritative when persistence is enabled. Never fall back
            # to a process-local copy if the one-time database state is missing.
            row = self.repository.consume_google_oauth_state_by_state(state_value)
            if row:
                state_row = {"state": str(row[0]), "organization_id": str(row[1]), "user_id": str(row[2]),
                             "code_verifier": str(row[3]), "expires_at": row[4]}
        else:
            state_row = self.store.google_oauth_states.pop(state_value, None)
        if not state_row:
            raise APIError(400, "GOOGLE_OAUTH_STATE_INVALID", "Google OAuth state is invalid or already used")
        from datetime import datetime
        expires = state_row["expires_at"]
        expires = expires if isinstance(expires, datetime) else datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
        if expires.tzinfo is None:
            from datetime import timezone
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= utc_now():
            raise APIError(400, "GOOGLE_OAUTH_STATE_INVALID", "Google OAuth state has expired")
        if error_value:
            return 302, {"Location": "/client?page=client-monitoring&google=denied", "Cache-Control": "no-store"}, b""
        if not code:
            raise APIError(400, "GOOGLE_OAUTH_INVALID", "Google OAuth callback is missing the authorization code")
        org_id = str(state_row["organization_id"])
        user_id = str(state_row["user_id"])
        oauth_client, _ = self._google_oauth()
        try:
                        token = oauth_client.exchange_code(code=code,
                 redirect_uri=self.config.public_base_url.rstrip("/") + "/v1/integrations/google/callback",
                code_verifier=str(state_row["code_verifier"]))
        except (GoogleAPIError, GoogleIntegrationError) as exc:
            raise APIError(502, "GOOGLE_TOKEN_EXCHANGE_FAILED", "Google authorization could not be completed") from exc
        from datetime import datetime, timezone
        from cryptography.fernet import Fernet
        cipher = Fernet(self._google_secret())
        connection_id = str(uuid.uuid4())
        connection = {"connection_id": connection_id, "google_account_id": None, "google_location_id": None,
                      "location_title": None, "encrypted_access_token": cipher.encrypt(token.access_token.encode()).decode(),
                      "encrypted_refresh_token": cipher.encrypt(token.refresh_token.encode()).decode() if token.refresh_token else None,
                      "expires_at": datetime.fromtimestamp(token.expires_at, timezone.utc).isoformat(),
                      "status": "CONNECTED", "created_by": user_id, "updated_at": utc_now().isoformat()}
        self.store.google_connections[(org_id, connection_id)] = connection
        if self.repository is not None and hasattr(self.repository, "save_google_connection"):
            self.repository.save_google_connection(org_id, connection)
        self.store.audit_event(org_id, user_id, "GOOGLE_CONNECTED", "google_connection:" + connection_id)
        if self.repository is not None and hasattr(self.repository, "security_event"):
            self.repository.security_event(org_id, user_id, "GOOGLE_CONNECTED", user_id, {"connection_id": connection_id})
        return 302, {"Location": "/client?page=client-monitoring&google=connected", "Cache-Control": "no-store", "Pragma": "no-cache"}, b""

    def handle(self, environ):
        """Traite une requête et renvoie (status, headers, body).

        Cette méthode applique les règles API sans appeler start_response.
        __call__ adapte ensuite le tuple au protocole WSGI.
        Les endpoints sont regroupés par domaine fonctionnel ci-dessous.
        """
        path = urlsplit(environ.get("PATH_INFO", "/")).path.rstrip("/") or "/"
        method = environ.get("REQUEST_METHOD", "GET").upper()
        cookie_token = self._cookie_session_token(environ)
        authorization = environ.get("HTTP_AUTHORIZATION", "")
        cookie_authenticated = bool(
            cookie_token
            and not (
                isinstance(authorization, str)
                and authorization.startswith("Bearer ")
            )
        )
        csrf_exempt_paths = {
            "/v1/auth/login",
            "/v1/auth/register",
            "/v1/auth/recovery/request",
            "/v1/auth/recovery/reset",
            "/v1/auth/verify-email",
            "/v1/organization/invitations/accept",
            "/v1/paypal/webhook",
        }
        if (
            cookie_authenticated
            and method in {"POST", "PUT", "PATCH", "DELETE"}
            and path not in csrf_exempt_paths
        ):
            supplied_csrf = environ.get("HTTP_X_CSRF_TOKEN", "")
            expected_csrf = self._csrf_token(cookie_token)
            if not isinstance(supplied_csrf, str) or not hmac.compare_digest(
                supplied_csrf, expected_csrf
            ):
                raise APIError(403, "CSRF_INVALID", "valid CSRF token is required")
        if path.startswith("/v1/") and method in {"POST", "PUT", "PATCH"} and path != "/v1/paypal/webhook":
            content_type = environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                raise APIError(415, "UNSUPPORTED_MEDIA_TYPE", "application/json content type is required")
        if not self._allow_rate_limit(
            self.limiter, environ.get("REMOTE_ADDR", "unknown"), "request"
        ):
            raise APIError(429, "RATE_LIMITED", "rate limit exceeded")
        if method == "GET" and path == "/v1/auth/csrf":
            if not self.config.cookie_auth_enabled:
                raise APIError(404, "NOT_FOUND", "not found")
            raw_token = self._cookie_session_token(environ)
            if not raw_token:
                raise APIError(401, "AUTH_REQUIRED", "authentication required")
            return self._json(200, {"csrf_token": self._csrf_token(raw_token)})
        if method == "GET" and path == "/health":
            result = health_check(checks={"store": lambda: self.store is not None})
            return self._json(
                200 if result.status == "ok" else 503,
                {
                    "status": result.status,
                    "service": "review-defense",
                    "version": "6.40",
                    "checks": result.checks,
                    "checked_at": result.checked_at,
                },
            )
        if method == "GET" and path == "/metrics":
            # Prometheus-compatible metrics contain only aggregate operational data.
            configured = os.getenv("REVIEW_DEFENSE_METRICS_TOKEN")
            supplied = environ.get("HTTP_X_METRICS_TOKEN")
            if supplied is None:
                auth = environ.get("HTTP_AUTHORIZATION", "")
                if auth.startswith("Bearer "):
                    supplied = auth[7:].strip()
            if self.config.production and (not configured or supplied != configured):
                raise APIError(404, "NOT_FOUND", "not found")
            return self._metrics_response()
        if method == "GET" and path == "/ready":
            dependencies = {"http": "ok", "store": "ok"}
            if self.repository is not None and hasattr(self.repository, "ping"):
                try:
                    dependencies["database"] = "ok" if self.repository.ping() else "failed"
                except Exception:
                    dependencies["database"] = "error"
            status = "ready" if all(value == "ok" for value in dependencies.values()) else "not_ready"
            return self._json(200 if status == "ready" else 503, {"status": status, "dependencies": dependencies})
        # AUTHENTIFICATION : inscription, connexion et récupération de compte.
        if method == "POST" and path == "/v1/auth/recovery/request":
            body = self._body(environ)
            try:
                email = normalize_email(str(body.get("email", "")))
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            organization_id = self._persistent_uuid(body.get("organization_id", ""), "organization_id")
            if not organization_id:
                raise APIError(422, "VALIDATION_ERROR", "organization_id is required")
            if not self._allow_rate_limit(
                self.recovery_limiter, self._auth_key(environ, email), "recovery"
            ):
                raise APIError(429, "RECOVERY_RATE_LIMITED", "too many recovery requests")
            user = None
            if self.repository is not None:
                row = self.repository.get_user_by_email(organization_id, email)
                if row:
                    user = User(str(row[0]), organization_id, str(row[1]), str(row[2]), str(row[3]))
            else:
                user = next((u for u in self.store.users.values() if u.organization_id == organization_id and u.email == email), None)
            if user is not None:
                raw, token_hash = recovery_token()
                expires = utc_now() + __import__("datetime").timedelta(minutes=30)
                self.store.recovery_tokens[token_hash] = {
                    "organization_id": organization_id,
                    "user_id": user.user_id,
                    "expires_at": expires.isoformat(),
                    "used_at": None,
                }
                if self.repository is not None and hasattr(self.repository, "create_recovery_token"):
                    self.repository.create_recovery_token(organization_id, user.user_id, token_hash, expires.isoformat())
                self.store.audit_event(organization_id, None, "PASSWORD_RECOVERY_REQUESTED", f"user:{user.user_id}")
                if self.config.recovery_email_enabled:
                    try:
                        send_recovery_email(recipient=user.email, organization_id=organization_id, token=raw,
                                            base_url=self.config.public_base_url, config=self._smtp_config())
                        self.store.audit_event(organization_id, None, "PASSWORD_RECOVERY_EMAIL_SENT", f"user:{user.user_id}")
                    except RecoveryEmailError as exc:
                        self.store.audit_event(organization_id, None, "PASSWORD_RECOVERY_EMAIL_FAILED", f"user:{user.user_id}", error=str(exc))
                if os.getenv("REVIEW_DEFENSE_EXPOSE_RECOVERY_TOKEN", "false").lower() == "true" and self.config.environment != "production":
                    return self._json(200, {"status":"requested", "recovery_token":raw, "expires_at":expires.isoformat()})
            return self._json(200, {"status":"requested"})

        if method == "POST" and path == "/v1/auth/recovery/reset":
            body = self._body(environ)
            organization_id = self._persistent_uuid(body.get("organization_id", ""), "organization_id")
            token = str(body.get("recovery_token", ""))
            new_password = body.get("new_password", "")
            if not organization_id or not token:
                raise APIError(422, "VALIDATION_ERROR", "organization_id and recovery_token are required")
            token_hash = __import__("hashlib").sha256(token.encode()).hexdigest()
            row = self.store.recovery_tokens.get(token_hash)
            if row is None and self.repository is not None and hasattr(self.repository, "get_recovery_token"):
                dbrow = self.repository.get_recovery_token(organization_id, token_hash)
                if dbrow:
                    row = {"recovery_id":str(dbrow[0]),"organization_id":str(dbrow[1]),"user_id":str(dbrow[2]),"expires_at":dbrow[3],"used_at":dbrow[4]}
                    self.store.recovery_tokens[token_hash] = row
            if row is None or row.get("organization_id") != organization_id or row.get("used_at"):
                raise APIError(400, "RECOVERY_INVALID", "recovery token is invalid")
            from datetime import datetime
            exp = row["expires_at"] if isinstance(row["expires_at"], datetime) else datetime.fromisoformat(str(row["expires_at"]).replace("Z","+00:00"))
            if exp <= utc_now():
                raise APIError(400, "RECOVERY_EXPIRED", "recovery token has expired")
            try:
                new_hash = hash_password(new_password)
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            user = self.store.users.get(row["user_id"])
            if user is None and self.repository is not None and hasattr(self.repository, "get_user_by_id"):
                urow = self.repository.get_user_by_id(organization_id, row["user_id"])
                if urow:
                    user = User(str(urow[0]), organization_id, str(urow[1]), str(urow[2]), str(urow[3]))
            if user is None:
                raise APIError(400, "RECOVERY_INVALID", "recovery token is invalid")
            if self.repository is not None:
                reset = getattr(self.repository, "reset_password_with_recovery_token", None)
                if reset is None:
                    raise APIError(503, "RECOVERY_NOT_SUPPORTED", "atomic password recovery is not available")
                reset_user_id = reset(organization_id, token_hash, new_hash)
                if not reset_user_id or str(reset_user_id) != user.user_id:
                    raise APIError(400, "RECOVERY_INVALID", "recovery token is invalid")
                self.store.users[user.user_id] = User(
                    user.user_id, user.organization_id, user.email, new_hash, user.role
                )
                row["used_at"] = utc_now().isoformat()
            else:
                # Memory mode has no database transaction; serialize the final
                # consume-and-update section and re-check the token under lock.
                with self._idem_lock:
                    if row.get("used_at"):
                        raise APIError(400, "RECOVERY_INVALID", "recovery token is invalid")
                    current_expiry = row["expires_at"]
                    if not isinstance(current_expiry, datetime):
                        current_expiry = datetime.fromisoformat(
                            str(current_expiry).replace("Z", "+00:00")
                        )
                    if current_expiry <= utc_now():
                        raise APIError(400, "RECOVERY_EXPIRED", "recovery token has expired")
                    self.store.users[user.user_id] = User(
                        user.user_id, user.organization_id, user.email, new_hash, user.role
                    )
                    row["used_at"] = utc_now().isoformat()
            for th, sess in list(self.store.sessions.items()):
                if sess.user_id == user.user_id and sess.organization_id == organization_id:
                    self.store.sessions[th] = Session(
                        sess.user_id, sess.organization_id, sess.role,
                        sess.token_hash, sess.expires_at, utc_now()
                    )
            self.store.audit_event(
                organization_id, user.user_id, "PASSWORD_RECOVERED", f"user:{user.user_id}"
            )
            return self._json(200, {"status": "password_reset"})

        if method == "POST" and path == "/v1/auth/email-verification/verify":
            body = self._body(environ)
            organization_id = self._persistent_uuid(body.get("organization_id", ""), "organization_id")
            token = str(body.get("verification_token", ""))
            if not organization_id or not token:
                raise APIError(422, "VALIDATION_ERROR", "organization_id and verification_token are required")
            token_hash = hash_token(token)
            row = self.store.email_verification_tokens.get(token_hash)
            if row is None and self.repository is not None and hasattr(self.repository, "get_email_verification_token"):
                dbrow = self.repository.get_email_verification_token(organization_id, token_hash)
                if dbrow:
                    row = {"verification_id": str(dbrow[0]), "organization_id": str(dbrow[1]), "user_id": str(dbrow[2]),
                           "expires_at": dbrow[3], "used_at": dbrow[4]}
                    self.store.email_verification_tokens[token_hash] = row
            if row is None or row.get("organization_id") != organization_id or row.get("used_at"):
                raise APIError(400, "VERIFICATION_INVALID", "verification token is invalid")
            from datetime import datetime
            exp = row["expires_at"] if isinstance(row["expires_at"], datetime) else datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
            if exp <= utc_now():
                raise APIError(400, "VERIFICATION_EXPIRED", "verification token has expired")
            user_id = str(row["user_id"])
            self.store.email_verified[user_id] = True
            row["used_at"] = utc_now().isoformat()
            if self.repository is not None:
                if hasattr(self.repository, "mark_email_verified"):
                    self.repository.mark_email_verified(organization_id, user_id)
                if hasattr(self.repository, "consume_email_verification_token"):
                    self.repository.consume_email_verification_token(
                        organization_id,
                        token_hash,
                    )
                if hasattr(self.repository, "security_event"):
                    self.repository.security_event(organization_id, user_id, "EMAIL_VERIFIED", user_id)
            self.store.audit_event(organization_id, user_id, "EMAIL_VERIFIED", f"user:{user_id}")
            return self._json(200, {"status": "email_verified"})

        if method == "POST" and path == "/v1/auth/register":
            body = self._body(environ)
            try:
                email = normalize_email(str(body.get("email", "")))
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            organization_name = str(body.get("organization_name", "")).strip()
            password = body.get("password", "")
            if not organization_name or len(organization_name) > 200:
                raise APIError(422, "VALIDATION_ERROR", "organization_name is required")
            try:
                password_hash = hash_password(password)
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            if self.repository is not None and hasattr(self.repository, "create_organization_and_owner"):
                try:
                    organization_id, uid, em, ph, role = self.repository.create_organization_and_owner(
                        organization_name, email, password_hash
                    )
                except Exception as exc:
                    if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
                        raise APIError(409, "ACCOUNT_EXISTS", "an account with this email already exists") from exc
                    raise
            else:
                organization_id = str(uuid.uuid4())
                uid = str(uuid.uuid4())
                user = User(uid, organization_id, email, password_hash, "OWNER")
                self.store.users[uid] = user
                self.store.email_verified[uid] = False
                self.store.audit_event(organization_id, uid, "ACCOUNT_CREATED", f"user:{uid}")
                if self.config.require_email_verification:
                    if not self.config.recovery_email_enabled:
                        raise APIError(503, "EMAIL_DELIVERY_NOT_CONFIGURED", "authentication email delivery is not configured")
                    raw_verification, expires_verification = self._issue_email_verification(user)
                    try:
                        send_verification_email(recipient=email, organization_id=organization_id, token=raw_verification,
                                                base_url=self.config.public_base_url, config=self._smtp_config())
                    except RecoveryEmailError as exc:
                        raise APIError(503, "EMAIL_DELIVERY_FAILED", "verification email could not be delivered") from exc
                    return self._json(201, {"status": "verification_required", "organization_id": organization_id,
                                            "expires_at": expires_verification})
            user = User(str(uid), str(organization_id), email, password_hash, "OWNER")
            self.store.users[user.user_id] = user
            self.store.email_verified[user.user_id] = not self.config.require_email_verification
            self.store.audit_event(user.organization_id, user.user_id, "ACCOUNT_CREATED", f"user:{user.user_id}")
            if self.repository is not None and self.config.require_email_verification:
                raw_verification, expires_verification = self._issue_email_verification(user)
                try:
                    send_verification_email(recipient=email, organization_id=organization_id, token=raw_verification,
                                            base_url=self.config.public_base_url, config=self._smtp_config())
                except RecoveryEmailError as exc:
                    raise APIError(503, "EMAIL_DELIVERY_FAILED", "verification email could not be delivered") from exc
                return self._json(201, {"status": "verification_required", "organization_id": organization_id,
                                        "expires_at": expires_verification})
            raw, session = issue_session(user_id=user.user_id, organization_id=user.organization_id,
                                         role=user.role, ttl_seconds=self.session_ttl)
            self.store.sessions[session.token_hash] = session
            if self.repository is not None and hasattr(self.repository, "put_session"):
                self.repository.put_session(user.organization_id, session.token_hash, user.user_id,
                                            user.role, session.expires_at.isoformat())
            return self._json(201, {"status": "created", "access_token": raw, "token_type": "Bearer",
                                    "expires_at": session.expires_at.isoformat(), "role": user.role,
                                    "organization_id": user.organization_id})
        if method == "POST" and path == "/v1/auth/login":
            body = self._body(environ)
            try:
                email = normalize_email(str(body.get("email", "")))
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            if not self._allow_rate_limit(
                self.auth_limiter, self._auth_key(environ, email), "authentication"
            ):
                raise APIError(429, "AUTH_RATE_LIMITED", "too many authentication attempts")
            password = body.get("password", "")
            user = None
            organization_id = self._persistent_uuid(body.get("organization_id", ""), "organization_id")
            if self.repository is not None:
                if not organization_id:
                    raise APIError(422, "VALIDATION_ERROR", "organization_id is required for persistent authentication")
                row = self.repository.get_user_by_email(organization_id, email)
                if row:
                    uid, em, ph, role = row
                    user = User(str(uid), organization_id, str(em), ph, str(role))
                    self.store.users[user.user_id] = user
            else:
                user = next((u for u in self.store.users.values() if u.email == email), None)
            if user is None or not isinstance(password, str) or not verify_password(password, user.password_hash):
                raise APIError(401, "AUTH_INVALID", "invalid credentials")
            if self.config.require_email_verification and not self._email_verified(user):
                raise APIError(403, "EMAIL_NOT_VERIFIED", "email verification is required before login")
            # MFA is reserved for privileged administration accounts.
            # Client-facing roles must never be blocked by an MFA enrollment left
            # over from an older account policy.
            mfa_secret = self._mfa_secret(user) if user.role in {"OWNER", "ADMIN"} else None
            if mfa_secret is not None:
                if not self._consume_mfa_code(user, str(body.get("mfa_code", ""))):
                    raise APIError(401, "MFA_REQUIRED", "valid MFA code is required")
            raw, session = issue_session(user_id=user.user_id, organization_id=user.organization_id, role=user.role, ttl_seconds=self.session_ttl)
            hashed = session.token_hash
            self.store.sessions[hashed] = session
            ua, iph = self._user_agent(environ), self._client_ip_hash(environ)
            if self.repository is not None:
                self.repository.put_session(user.organization_id, hashed, user.user_id, user.role, session.expires_at.isoformat(), ua, iph)
                if hasattr(self.repository, "security_event"):
                    self.repository.security_event(user.organization_id, user.user_id, "LOGIN", user.user_id, {"user_agent": ua, "ip_hash": iph})
            self.store.audit_event(user.organization_id, user.user_id, "LOGIN", "session")
            return self._json(200, {"access_token": raw, "token_type": "Bearer", "expires_at": session.expires_at.isoformat(), "role": user.role})

        if method == "POST" and path == "/v1/organization/invitations/accept":
            body = self._body(environ)
            try:
                email = normalize_email(str(body.get("email", "")))
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            organization_id = self._persistent_uuid(body.get("organization_id", ""), "organization_id")
            token = str(body.get("invitation_token", ""))
            password = body.get("password", "")
            token_hash = hash_token(token)
            invitation = next((i for i in self.store.invitations.values() if i.get("token_hash") == token_hash), None)
            if invitation is None and self.repository is not None and organization_id and hasattr(self.repository, "get_invitation_by_token"):
                dbrow = self.repository.get_invitation_by_token(organization_id, token_hash)
                if dbrow:
                    invitation = {
                        "invitation_id": str(dbrow[0]), "organization_id": str(dbrow[1]),
                        "email": str(dbrow[2]), "role": str(dbrow[3]), "token_hash": str(dbrow[4]),
                        "expires_at": dbrow[5].isoformat() if hasattr(dbrow[5], "isoformat") else str(dbrow[5]),
                        "invited_by": str(dbrow[6]), "accepted_at": dbrow[7], "revoked_at": dbrow[8],
                    }
                    self.store.invitations[invitation["invitation_id"]] = invitation
            if (invitation is None or invitation.get("organization_id") != organization_id
                    or invitation.get("email") != email or invitation.get("accepted_at") or invitation.get("revoked_at")):
                raise APIError(400, "INVITATION_INVALID", "invitation is invalid or already used")
            from datetime import datetime
            if datetime.fromisoformat(invitation["expires_at"]) <= utc_now():
                raise APIError(400, "INVITATION_EXPIRED", "invitation has expired")
            try:
                ph = hash_password(password)
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            existing = next((u for u in self.store.users.values() if u.email == email and u.organization_id == invitation["organization_id"]), None)
            if existing:
                uid=existing.user_id
                self.store.users[uid]=User(uid, existing.organization_id, existing.email, ph, invitation["role"])
                for th,sess in list(self.store.sessions.items()):
                    if sess.user_id==uid and sess.organization_id==existing.organization_id:
                        self.store.sessions[th]=Session(sess.user_id,sess.organization_id,sess.role,sess.token_hash,sess.expires_at,utc_now())
                if self.repository is not None:
                    if hasattr(self.repository,"update_password"):
                        self.repository.update_password(invitation["organization_id"],uid,ph)
                    if hasattr(self.repository,"update_role"):
                        self.repository.update_role(invitation["organization_id"],uid,invitation["role"])
            else:
                uid=str(uuid.uuid4())
                new_user=User(uid,invitation["organization_id"],email,ph,invitation["role"])
                self.store.users[uid]=new_user
                if self.repository is not None and hasattr(
                    self.repository,
                    "create_user",
                ):
                    rid, *_ = self.repository.create_user(
                        invitation["organization_id"],
                        email,
                        ph,
                        invitation["role"],
                    )
                    self.store.users.pop(uid, None)
                    uid = str(rid)
                    self.store.users[uid] = User(
                        uid,
                        invitation["organization_id"],
                        email,
                        ph,
                        invitation["role"],
                    )
            invitation["accepted_at"]=utc_now().isoformat()
            if self.repository is not None and hasattr(self.repository, "mark_invitation_accepted"):
                if not self.repository.mark_invitation_accepted(invitation["organization_id"], invitation["invitation_id"]):
                    raise APIError(409, "INVITATION_STATE_CONFLICT", "invitation could not be accepted")
            self.store.email_verified[uid] = False
            if self.repository is not None and hasattr(self.repository, "set_email_unverified"):
                self.repository.set_email_unverified(invitation["organization_id"], uid)
            if self.config.require_email_verification:
                if not self.config.recovery_email_enabled:
                    raise APIError(503, "EMAIL_DELIVERY_NOT_CONFIGURED", "authentication email delivery is not configured")
                raw_verification, expires_verification = self._issue_email_verification(self.store.users[uid])
                try:
                    send_verification_email(recipient=email, organization_id=invitation["organization_id"], token=raw_verification,
                                            base_url=self.config.public_base_url, config=self._smtp_config())
                except RecoveryEmailError as exc:
                    raise APIError(503, "EMAIL_DELIVERY_FAILED", "verification email could not be delivered") from exc
                self.store.audit_event(invitation["organization_id"], uid, "EMAIL_VERIFICATION_EMAIL_SENT", f"user:{uid}")
                return self._json(200, {"status":"verification_required", "expires_at":expires_verification})
            raw, session = issue_session(user_id=uid, organization_id=invitation["organization_id"], role=invitation["role"], ttl_seconds=self.session_ttl)
            self.store.sessions[session.token_hash]=session
            if self.repository is not None and hasattr(self.repository,"put_session"):
                self.repository.put_session(invitation["organization_id"],session.token_hash,uid,invitation["role"],session.expires_at.isoformat())
            self.store.audit_event(invitation["organization_id"],uid,"INVITATION_ACCEPTED",f"invitation:{invitation['invitation_id']}")
            return self._json(
                200,
                {
                    "status": "accepted",
                    "access_token": raw,
                    "token_type": "Bearer",
                    "expires_at": session.expires_at.isoformat(),
                    "role": invitation["role"],
                },
            )

        # WEBHOOKS DE PAIEMENT : événements entrants traités après vérification.
        if method == "POST" and path == "/v1/paypal/webhook":
            length=int(environ.get("CONTENT_LENGTH") or 0)
            if length > 1000000:
                raise APIError(413,"PAYLOAD_TOO_LARGE","webhook payload too large")
            raw=environ["wsgi.input"].read(length)
            try:
                verified, event = paypal_verify_webhook(
                    raw_body=raw,
                    headers={
                        "paypal-" + key[len("HTTP_PAYPAL_"):].lower().replace("_", "-"): value
                        for key, value in environ.items()
                        if key.startswith("HTTP_PAYPAL_")
                    },
                )
            except (PayPalError, ValueError, KeyError) as exc:
                raise APIError(
                    400,
                    "PAYPAL_WEBHOOK_INVALID",
                    "invalid PayPal webhook",
                ) from exc
            if not verified:
                raise APIError(400,"PAYPAL_WEBHOOK_INVALID","PayPal webhook signature verification failed")
            event_id=str(event.get("id","")).strip()
            if not event_id:
                raise APIError(400,"PAYPAL_WEBHOOK_INVALID","missing PayPal event id")
            event_type=str(event.get("event_type",""))
            resource=event.get("resource") or {}
            related_ids=((resource.get("supplementary_data") or {}).get("related_ids") or {})
            paypal_order_id=str(related_ids.get("order_id") or resource.get("order_id") or "")
            paypal_capture_id=str(resource.get("id") or "")
            paypal_id=paypal_order_id or paypal_capture_id
            if event_type.startswith("PAYMENT.SALE.") and resource.get("billing_agreement_id"):
                paypal_id=str(resource.get("billing_agreement_id"))
            if self.repository is not None and hasattr(self.repository,"billing_event_seen") and self.repository.billing_event_seen(event_id):
                return self._json(200,{"status":"accepted","duplicate":True})
            tx=None
            # Webhooks are authoritative status signals; resolve the locally recorded
            # PayPal identifier before mutating billing state.
            if self.repository is not None and paypal_id and hasattr(self.repository,"get_billing_by_paypal_id_global"):
                tx=self.repository.get_billing_by_paypal_id_global(paypal_id)
            if tx is None:
                for key,row in list(self.store.billing.items()):
                    if row.get("paypal_order_id")==paypal_id or row.get("paypal_subscription_id")==paypal_id:
                        tx=row
                        break
            if tx is not None:
                status_map = {
                    "CHECKOUT.ORDER.COMPLETED": "COMPLETED",
                    "PAYMENT.CAPTURE.COMPLETED": "COMPLETED",
                    "PAYMENT.CAPTURE.DENIED": "DENIED",
                    "PAYMENT.CAPTURE.PENDING": "PENDING",
                    "PAYMENT.SALE.COMPLETED": "ACTIVE",
                    "BILLING.SUBSCRIPTION.ACTIVATED": "ACTIVE",
                    "BILLING.SUBSCRIPTION.UPDATED": "ACTIVE",
                    "BILLING.SUBSCRIPTION.CANCELLED": "CANCELLED",
                    "BILLING.SUBSCRIPTION.SUSPENDED": "SUSPENDED",
                    "BILLING.SUBSCRIPTION.EXPIRED": "EXPIRED",
                    "BILLING.SUBSCRIPTION.PAYMENT.FAILED": "PAYMENT_FAILED",
                    "PAYMENT.SALE.REFUNDED": "REFUNDED",
                    "PAYMENT.SALE.REVERSED": "REVERSED",
                    "PAYMENT.CAPTURE.REFUNDED": "REFUNDED",
                    "PAYMENT.CAPTURE.REVERSED": "REVERSED",
                }
                tx["status"]=status_map.get(event_type,tx.get("status","PENDING"))
                tx["paypal_event_id"]=event_id
                existing_metadata=tx.get("metadata") if isinstance(tx.get("metadata"),dict) else {}
                tx["paypal_order_id"]=paypal_order_id or tx.get("paypal_order_id")
                tx["metadata"]={**existing_metadata,"last_webhook_type":event_type,"last_webhook_at":utc_now().isoformat(),
                                **({"paypal_capture_id":paypal_capture_id} if paypal_capture_id and paypal_capture_id != paypal_id else {})}
                if self.repository is not None:
                    try:
                        self.repository.update_billing_transaction(tx["organization_id"],tx)
                    except Exception as exc:
                        raise APIError(
                            500,
                            "BILLING_WEBHOOK_PERSIST_FAILED",
                            "PayPal webhook was verified but billing state could not be persisted; "
                            "PayPal should retry.",
                        ) from exc
                if tx.get("kind") == "subscription" and tx.get("offer_id"):
                    acct={"organization_id":tx["organization_id"],"plan_code":plan_for_offer(tx["offer_id"]).code,
                          "status":account_status({"status":tx.get("status")}),
                          "paypal_subscription_id":tx.get("paypal_subscription_id"),
                          "offer_id":tx.get("offer_id")}
                    self.billing_accounts[tx["organization_id"]]=acct
                    event_row={"event_id":str(uuid.uuid4()),"paypal_event_id":event_id,
                               "paypal_subscription_id":tx.get("paypal_subscription_id"),
                               "event_type":event_type,"status":tx.get("status"),
                               "offer_id":tx.get("offer_id"),"payload":event}
                    self.billing_events.append(event_row)
                    if self.repository is not None:
                        if hasattr(self.repository,"upsert_billing_account"):
                            self.repository.upsert_billing_account(tx["organization_id"],acct)
                        if hasattr(self.repository,"create_billing_event"):
                            self.repository.create_billing_event(tx["organization_id"],event_row)
                    self.store.audit_event(
                        tx["organization_id"],
                        None,
                        "PAYPAL_WEBHOOK_PROCESSED",
                        f"billing:{tx['id']}",
                        event_type=event_type,
                        paypal_id=paypal_id,
                    )
            return self._json(200,{"status":"accepted"})
        # GOOGLE BUSINESS PROFILE : OAuth et sélection des établissements.
        if method == "GET" and path == "/v1/integrations/google/callback":
            return self._google_callback(environ)
        user = self._auth(environ)
        self._validate_persistent_resource_path(path)
        # All v1 routes are tenant-bound to the authenticated user. There is no organization_id override.


        if method in {"GET", "POST"} and path == "/v1/integrations/google/start":
            self._require_role(user, "OWNER", "ADMIN", "CLIENT")
            oauth_client, state_manager = self._google_oauth()
            authorization = state_manager.create(
                client_id=oauth_client.client_id,
                redirect_uri=(
                    self.config.public_base_url.rstrip("/")
                    + "/v1/integrations/google/callback"
                ),
            )
            from datetime import timedelta
            expires_at = (utc_now() + timedelta(seconds=state_manager.ttl_seconds)).isoformat()
            state_row = {"state": authorization.state, "organization_id": user.organization_id, "user_id": user.user_id,
                         "code_verifier": authorization.code_verifier, "expires_at": expires_at}
            self.store.google_oauth_states[authorization.state] = state_row
            if self.repository is not None and hasattr(self.repository, "save_google_oauth_state"):
                self.repository.save_google_oauth_state(user.organization_id, authorization.state, user.user_id, authorization.code_verifier, expires_at)
            self.store.audit_event(user.organization_id, user.user_id, "GOOGLE_OAUTH_STARTED", "google_oauth")
            if method == "POST":
                return self._json(200, {"authorization_url": authorization.authorization_url}, {"Cache-Control": "no-store", "Pragma": "no-cache"})
            return 302, {"Location": authorization.authorization_url, "Cache-Control": "no-store", "Pragma": "no-cache"}, b""

        if method == "GET" and path == "/v1/integrations/google/locations":
            connections = self._google_connections(user.organization_id)
            items, errors = [], []
            for connection in connections:
                connection_id = str(connection["connection_id"])
                try:
                    access_token, current = self._google_access_token(user.organization_id, connection_id)
                    client = GoogleBusinessProfileClient(organization_id=user.organization_id, access_token=access_token)
                    accounts, account_page = client.list_accounts()
                    pages = 0
                    while account_page and pages < 9:
                        more, account_page = client.list_accounts(page_token=account_page)
                        accounts += more
                        pages += 1
                    for account in accounts:
                        locations, location_page = client.list_locations(account.name)
                        pages = 0
                        while location_page and pages < 9:
                            more, location_page = client.list_locations(account.name, page_token=location_page)
                            locations += more
                            pages += 1
                        for location in locations:
                            items.append({"connection_id": connection_id, "account_id": account.name, "account_name": account.account_name or account.name,
                                          "location_id": location.name, "location_name": location.location_name or location.name,
                                          "selected": current.get("google_account_id") == account.name and current.get("google_location_id") == location.name})
                except APIError as exc:
                    errors.append({"connection_id": connection_id, "code": exc.code, "message": exc.message})
                except (GoogleAPIError, GoogleIntegrationError) as exc:
                    errors.append({"connection_id": connection_id, "code": "GOOGLE_UPSTREAM_ERROR", "message": "Google locations could not be loaded"})
            return self._json(
                200,
                {
                    "items": items,
                    "connections": [
                        {
                            "connection_id": connection["connection_id"],
                            "status": connection.get("status"),
                            "location_title": connection.get("location_title"),
                        }
                        for connection in connections
                    ],
                    "errors": errors,
                },
            )

        if method == "POST" and path == "/v1/integrations/google/select-location":
            self._require_role(user, "OWNER", "ADMIN", "CLIENT")
            body = self._body(environ)
            connection_id = self._persistent_uuid(body.get("connection_id", ""), "connection_id")
            account_id = str(body.get("account_id", "")).strip()
            location_id = str(body.get("location_id", "")).strip()
            if not connection_id or not account_id or not location_id:
                raise APIError(422, "VALIDATION_ERROR", "connection_id, account_id and location_id are required")
            access_token, connection = self._google_access_token(user.organization_id, connection_id)
            client = GoogleBusinessProfileClient(organization_id=user.organization_id, access_token=access_token)
            try:
                accounts, account_page = client.list_accounts()
                pages = 0
                while account_page and pages < 9:
                    more, account_page = client.list_accounts(page_token=account_page)
                    accounts += more
                    pages += 1
                account = next((x for x in accounts if x.name == account_id), None)
                if account is None:
                    raise APIError(403, "GOOGLE_LOCATION_FORBIDDEN", "Google account does not belong to this connection")
                locations, location_page = client.list_locations(account_id)
                pages = 0
                while location_page and pages < 9:
                    more, location_page = client.list_locations(account_id, page_token=location_page)
                    locations += more
                    pages += 1
                location = next((x for x in locations if x.name == location_id), None)
                if location is None:
                    raise APIError(403, "GOOGLE_LOCATION_FORBIDDEN", "Google location does not belong to this account")
                sync = client.list_reviews(account_id, location_id, page_size=50, order_by="updateTime desc")
            except APIError:
                raise
            except (GoogleAPIError, GoogleIntegrationError) as exc:
                raise APIError(502, "GOOGLE_UPSTREAM_ERROR", "Google location could not be selected or synchronized") from exc
            connection["google_account_id"] = account_id
            connection["google_location_id"] = location_id
            connection["location_title"] = location.location_name or location.name
            connection["updated_at"] = utc_now().isoformat()
            self.store.google_connections[(user.organization_id, connection_id)] = connection
            if self.repository is not None and hasattr(self.repository, "save_google_connection"):
                self.repository.save_google_connection(user.organization_id, connection)
            for review in sync.items:
                self.store.reviews[(user.organization_id, review.review_id)] = review
                if self.repository is not None and hasattr(self.repository, "upsert_review"):
                    self.repository.upsert_review(user.organization_id, asdict(review))
            self.store.audit_event(user.organization_id, user.user_id, "GOOGLE_LOCATION_SELECTED", "google_connection:" + connection_id,
                                   account_id=account_id, location_id=location_id, reviews_synced=len(sync.items))
            return self._json(200, {"status": "selected", "connection_id": connection_id, "location_id": location_id, "reviews_synced": len(sync.items)})

        # ESPACE CLIENT : profil de l'organisation et documents associés.
        if method == "GET" and path == "/v1/client/profile":
            return self._json(200, {"profile": self._client_profile(user.organization_id)})

        if method == "POST" and path == "/v1/client/profile":
            self._require_role(user, "OWNER", "ADMIN", "CLIENT")
            body = self._body(environ)
            fields = ("legal_name", "website", "phone", "address", "city", "postal_code", "country", "sector", "employee_count", "description")
            profile = {}
            limits = {
                "legal_name": 200,
                "website": 500,
                "phone": 60,
                "address": 300,
                "city": 120,
                "postal_code": 30,
                "country": 100,
                "sector": 120,
                "employee_count": 60,
                "description": 2000,
            }
            for key in fields:
                value = str(body.get(key, "")).strip()
                if len(value) > limits[key]:
                    raise APIError(422, "VALIDATION_ERROR", key + " is too long")
                profile[key] = value or None
            if profile.get("website"):
                website = profile["website"]
                # A bare hostname may omit its scheme, but a URI scheme such as
                # javascript: must never be reinterpreted as a hostname.
                scheme_like = re.match(r"^[a-z][a-z0-9+.-]*:", website, re.IGNORECASE)
                host_with_port = re.match(r"^[a-z0-9.-]+:\\d+(?:/|$)", website, re.IGNORECASE)
                if scheme_like and ":
                    //" not in website and not host_with_port:
                    raise APIError(422, "VALIDATION_ERROR", "website must be a valid http(s) URL")
                parsed = urlsplit(website if "://" in website else "https://" + website)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc or "@" in parsed.netloc:
                    raise APIError(422, "VALIDATION_ERROR", "website must be a valid http(s) URL")
            self.store.organization_profiles[user.organization_id] = profile
            if self.repository is not None and hasattr(self.repository, "upsert_organization_profile"):
                row = self.repository.upsert_organization_profile(user.organization_id, profile)
                if row:
                    profile = dict(zip(fields + ("updated_at",), row))
                    self.store.organization_profiles[user.organization_id] = profile
            self.store.audit_event(user.organization_id, user.user_id, "CLIENT_PROFILE_UPDATED", "organization:" + user.organization_id)
            return self._json(200, {"profile": profile})

        if method == "GET" and path == "/v1/client/documents":
            documents = self._client_document_rows(user.organization_id)
            safe = [
                {
                    "document_id": str(document.get("document_id")),
                    "filename": document.get("filename"),
                    "content_type": document.get("content_type"),
                    "size_bytes": int(document.get("size_bytes") or 0),
                    "sha256": document.get("sha256"),
                    "category": document.get("category"),
                    "created_at": _iso_value(document.get("created_at")),
                }
                for document in documents
            ]
            return self._json(200, {"items": safe, "count": len(safe)})

        if method == "POST" and path == "/v1/client/documents":
            self._require_role(user, "OWNER", "ADMIN", "CLIENT")
            body = self._body(environ)
            filename = str(body.get("filename", "")).strip()
            content_type = str(body.get("content_type", "")).strip().lower()
            encoded = str(body.get("content_base64", "")).strip()
            category = str(body.get("category", "GENERAL")).strip().upper()
            if (
                not filename
                or len(filename) > 255
                or filename != os.path.basename(filename)
                or "/" in filename
                or "\\" in filename
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in filename)
            ):
                raise APIError(422, "VALIDATION_ERROR", "filename is invalid")
            if not encoded or len(encoded) > ((MAX_UPLOAD_BYTES + 2) // 3) * 4 + 8:
                raise APIError(413, "PAYLOAD_TOO_LARGE", "document exceeds the upload limit")
            if category not in {"GENERAL", "IDENTITY", "COMPANY", "CONTRACT", "INVOICE", "OTHER"}:
                raise APIError(422, "VALIDATION_ERROR", "document category is invalid")
            try:
                content = base64.b64decode(encoded, validate=True)
                validate_upload(
                    size_bytes=len(content),
                    content_type=content_type,
                    filename=filename,
                    content=content,
                )
            except (ValueError, TypeError) as exc:
                raise APIError(422, "INVALID_UPLOAD", str(exc)) from exc
            document_id = str(uuid.uuid4())
            try:
                stored = self.store.vault.put(
                    organization_id=user.organization_id,
                    evidence_id=document_id,
                    content=content,
                    content_type=content_type,
                    filename=filename,
                )
            except (ValueError, PermissionError) as exc:
                raise APIError(422, "INVALID_UPLOAD", str(exc)) from exc
            document = {
                "document_id": document_id,
                "organization_id": user.organization_id,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": stored.size_bytes,
                "sha256": stored.sha256,
                "object_key": stored.object_key,
                "category": category,
                "created_by": user.user_id,
                "created_at": stored.created_at.isoformat(),
            }
            try:
                if self.repository is not None and hasattr(
                    self.repository,
                    "put_client_document",
                ):
                    self.repository.put_client_document(
                        user.organization_id,
                        document,
                    )
                self.store.client_documents[
                    (user.organization_id, document_id)
                ] = document
            except Exception:
                self.store.vault.delete(
                    organization_id=user.organization_id,
                    object_key=stored.object_key,
                )
                raise
            self.store.audit_event(
                user.organization_id,
                user.user_id,
                "CLIENT_DOCUMENT_UPLOADED",
                f"client_document:{document_id}",
                filename=filename,
                size_bytes=stored.size_bytes,
                sha256=stored.sha256,
            )
            return self._json(
                201,
                {
                    "document": {
                        "document_id": document_id,
                        "filename": filename,
                        "content_type": content_type,
                        "size_bytes": stored.size_bytes,
                        "sha256": stored.sha256,
                        "category": category,
                    }
                },
            )

        if method == "GET" and path.startswith("/v1/client/documents/") and path.endswith("/download"):
            document_id = path.split("/")[-2]
            document = next((d for d in self._client_document_rows(user.organization_id) if str(d.get("document_id")) == document_id), None)
            if not document:
                raise APIError(404, "NOT_FOUND", "document not found")
            try:
                content = self.store.vault.get(organization_id=user.organization_id, object_key=str(document["object_key"]))
            except (KeyError, PermissionError, OSError) as exc:
                raise APIError(404, "DOCUMENT_UNAVAILABLE", "document content is unavailable") from exc
            safe_name = "".join(
                character if 32 <= ord(character) < 127 else "_"
                for character in str(document["filename"])
            ).replace('"', "")
            return (
                200,
                {
                    "Content-Type": str(document["content_type"]),
                    "Content-Length": str(len(content)),
                    "Content-Disposition": f'attachment; filename="{safe_name}"',
                    "X-Content-Type-Options": "nosniff",
                },
                content,
            )

        # FACTURATION : catalogue, abonnement et opérations PayPal.
        if method == "GET" and path == "/v1/billing":
            rows=list(self.store.billing.values())
            account=self.billing_accounts.get(user.organization_id)
            events=list(self.billing_events)
            if self.repository is not None:
                if hasattr(self.repository,"list_billing_transactions"):
                    rows=self.repository.list_billing_transactions(user.organization_id,user.user_id)
                if hasattr(self.repository,"get_billing_account"):
                    account=self.repository.get_billing_account(user.organization_id) or account
                if hasattr(self.repository,"list_billing_events"):
                    events=self.repository.list_billing_events(user.organization_id)
            return self._json(200,{"account":account,"items":rows,"events":events,"count":len(rows),"paypal_configured":paypal_configured()})
        if method == "GET" and path == "/v1/billing/plans":
            return self._json(200,{"items":public_plans()})
        if method == "GET" and path == "/v1/billing/events":
            events=list(self.billing_events)
            if self.repository is not None and hasattr(self.repository,"list_billing_events"):
                events=self.repository.list_billing_events(user.organization_id)
            return self._json(200,{"items":events,"count":len(events)})
        if method == "GET" and path == "/v1/billing/catalog":
            items = public_catalog()
            return self._json(200, {"items": items, "count": len(items)})
        if method == "GET" and path == "/v1/paypal/config":
                        return self._json(
                200,
                {
                    "configured": paypal_configured(),
                    "client_id": PAYPAL_SUBSCRIPTION_CLIENT_ID,
                    "environment": "live",
                    "diagnostics": paypal_configuration_status(),
                },
            )
        if method == "GET" and path == "/v1/paypal/subscription/config":
            offer_id=str(parse_qs(environ.get("QUERY_STRING","")).get("offer_id",[""])[0])
            try:
                offer=get_offer(offer_id)
            except ValueError as exc:
                raise APIError(422,"INVALID_OFFER","unknown subscription offer") from exc
            if offer.kind!="subscription":
                raise APIError(422,"INVALID_OFFER","not a subscription offer")
            plan_id=paypal_plan_id(offer)
            if not paypal_configured() or not plan_id:
                raise APIError(503,"PAYPAL_NOT_CONFIGURED","PayPal subscription plan is not configured")
            return self._json(
                200,
                {
                    "offer_id": offer.offer_id,
                    "plan_id": plan_id,
                    "client_id": PAYPAL_SUBSCRIPTION_CLIENT_ID,
                    "currency": offer.currency,
                    "amount": str(offer.amount),
                },
            )
        if method == "POST" and path == "/v1/paypal/subscription/confirm":
            body=self._body(environ)
            offer_id=str(body.get("offer_id","")).strip()
            subscription_id=str(body.get("subscription_id","")).strip()
            try:
                offer=get_offer(offer_id)
            except ValueError as exc:
                raise APIError(422,"INVALID_OFFER","unknown subscription offer") from exc
            if offer.kind != "subscription" or not subscription_id:
                raise APIError(
                    422,
                    "INVALID_SUBSCRIPTION",
                    "subscription and subscription offer are required",
                )
            plan_id=paypal_plan_id(offer)
            if not plan_id:
                raise APIError(503,"PAYPAL_NOT_CONFIGURED","subscription plan is not configured")
            existing_tx=next((x for x in self.store.billing.values() if x.get("paypal_subscription_id")==subscription_id),None)
            if existing_tx is None and self.repository is not None and hasattr(self.repository,"get_billing_by_paypal_id_global"):
                existing_tx=self.repository.get_billing_by_paypal_id_global(subscription_id)
            if existing_tx is not None:
                if str(existing_tx.get("organization_id","")) != str(user.organization_id):
                    raise APIError(409,"SUBSCRIPTION_ALREADY_LINKED","PayPal subscription is already linked to another organization")
                return self._json(
                    200,
                    {
                        "status": existing_tx.get("status", "CREATED"),
                        "subscription_id": subscription_id,
                        "offer_id": existing_tx.get("offer_id", offer.offer_id),
                        "existing": True,
                    },
                )
            try:
                pp=paypal_request_json("GET",f"/v1/billing/subscriptions/{subscription_id}",access_token=paypal_access_token())
            except PayPalError as exc:
                raise APIError(502,"PAYPAL_SUBSCRIPTION_LOOKUP_FAILED","PayPal subscription lookup failed",exc.payload)
            if str(pp.get("plan_id",""))!=plan_id:
                raise APIError(409,"SUBSCRIPTION_PLAN_MISMATCH","subscription plan does not match the selected offer")
            tx_id = str(uuid.uuid4())
            row = {"id":tx_id,
                "organization_id":user.organization_id,
                "user_id":user.user_id,
                "offer_id":offer.offer_id,
                "kind":"subscription",
                "status":pp.get("status",
                "CREATED"),
                "currency":offer.currency,
                "amount":str(offer.amount),
                "paypal_order_id":None,
                "paypal_subscription_id":subscription_id,
                "metadata":{"subscription":pp}}
            try:
                if self.repository is not None and hasattr(
                    self.repository,
                    "create_billing_transaction",
                ):
                    self.repository.create_billing_transaction(
                        user.organization_id,
                        row,
                    )
            except Exception as exc:
                self.store.audit_event(
                    user.organization_id,
                    user.user_id,
                    "PAYPAL_SUBSCRIPTION_LEDGER_FAILED",
                    f"billing:{tx_id}",
                    offer_id=offer.offer_id,
                    error_type=type(exc).__name__,
                )
                raise APIError(
                    500,
                    "BILLING_LEDGER_FAILED",
                    "PayPal subscription was created but could not be recorded. "
                    "Please retry; the subscription was not cancelled automatically.",
                ) from exc

            self.store.billing[tx_id] = row
            account = {
                "organization_id": user.organization_id,
                "plan_code": plan_for_offer(offer.offer_id).code,
                "status": account_status({"status": row["status"]}),
                "paypal_subscription_id": subscription_id,
                "offer_id": offer.offer_id,
            }
            self.billing_accounts[user.organization_id] = account
            if self.repository is not None and hasattr(
                self.repository,
                "upsert_billing_account",
            ):
                self.repository.upsert_billing_account(
                    user.organization_id,
                    account,
                )
            self.store.audit_event(
                user.organization_id,
                user.user_id,
                "PAYPAL_SUBSCRIPTION_CONFIRMED",
                f"billing:{tx_id}",
                paypal_subscription_id=subscription_id,
                offer_id=offer.offer_id,
            )
            return self._json(
                201,
                {
                    "status": row["status"],
                    "subscription_id": subscription_id,
                    "offer_id": offer.offer_id,
                },
            )

        # SÉCURITÉ DU COMPTE : MFA, vérification email et gestion des sessions.
        if method == "POST" and path == "/v1/auth/email-verification/request":
            if self._email_verified(user):
                return self._json(200, {"status": "already_verified"})
            if not self.config.recovery_email_enabled:
                raise APIError(503, "EMAIL_DELIVERY_NOT_CONFIGURED", "authentication email delivery is not configured")
            raw, expires_at = self._issue_email_verification(user)
            try:
                send_verification_email(recipient=user.email, organization_id=user.organization_id, token=raw,
                                        base_url=self.config.public_base_url, config=self._smtp_config())
            except RecoveryEmailError as exc:
                self.store.audit_event(user.organization_id, user.user_id, "EMAIL_VERIFICATION_EMAIL_FAILED", f"user:{user.user_id}", error=str(exc))
                raise APIError(503, "EMAIL_DELIVERY_FAILED", "verification email could not be delivered") from exc
            self.store.audit_event(user.organization_id, user.user_id, "EMAIL_VERIFICATION_EMAIL_SENT", f"user:{user.user_id}")
            return self._json(200, {"status": "sent", "expires_at": expires_at})
        if method == "POST" and path == "/v1/auth/mfa/enroll":
            self._require_role(user, "OWNER", "ADMIN")
            if self._mfa_state(user).get("enabled"):
                raise APIError(409, "MFA_ALREADY_ENABLED", "MFA is already enabled")
            secret = generate_secret()
            encrypted = encrypt_secret(secret, self._mfa_key())
            self.store.mfa[user.user_id] = {"enabled":False,"secret_enc":encrypted,"pending":True}
            if self.repository is not None and hasattr(self.repository,"set_mfa_secret"):
                self.repository.set_mfa_secret(user.organization_id,user.user_id,encrypted,False)
            self.store.audit_event(user.organization_id,user.user_id,"MFA_ENROLLMENT_STARTED",f"user:{user.user_id}")
            return self._json(200,{"status":"pending","secret":secret,"otpauth_uri":otpauth_uri(secret,user.email)})

        if method == "POST" and path == "/v1/auth/mfa/confirm":
            self._require_role(user, "OWNER", "ADMIN")
            state=self._mfa_state(user)
            if not state.get("secret_enc"):
                raise APIError(400,"MFA_NOT_ENROLLED","MFA enrollment has not been started")
            secret=decrypt_secret(state["secret_enc"],self._mfa_key())
            if not self._consume_mfa_code(user, str(self._body(environ).get("code",""))):
                raise APIError(401,"MFA_INVALID","invalid MFA code")
            state={"enabled":True,"secret_enc":state["secret_enc"]}
            self.store.mfa[user.user_id]=state
                        if self.repository is not None and hasattr(self.repository,
                "set_mfa_secret"): self.repository.set_mfa_secret(user.organization_id,
                user.user_id,
                state["secret_enc"],
                True)
            self.store.audit_event(user.organization_id,user.user_id,"MFA_ENABLED",f"user:{user.user_id}")
            return self._json(200,{"status":"enabled"})

        if method == "POST" and path == "/v1/auth/mfa/disable":
            self._require_role(user,"OWNER","ADMIN")
            body=self._body(environ)
            current=str(body.get("password",""))
            code=str(body.get("mfa_code",""))
            if not verify_password(current,user.password_hash):
                raise APIError(401,"AUTH_INVALID","password is invalid")
            secret=self._mfa_secret(user)
            if secret is not None and not verify_totp(secret,code):
                raise APIError(401,"MFA_INVALID","valid MFA code is required")
            self.store.mfa[user.user_id]={"enabled":False,"secret_enc":None}
            if self.repository is not None and hasattr(self.repository,"disable_mfa"):
                self.repository.disable_mfa(user.organization_id,user.user_id)
            self.store.audit_event(user.organization_id,user.user_id,"MFA_DISABLED",f"user:{user.user_id}")
            return self._json(200,{"status":"disabled"})

        # CONFIDENTIALITÉ : export, demandes et consentements de données.
        if method == "GET" and path == "/v1/privacy/export":
            payload = self._privacy_export(user)
            self.store.audit_event(user.organization_id, user.user_id, "PRIVACY_EXPORT_REQUESTED", f"user:{user.user_id}")
            return self._json(
                200,
                payload,
                {
                    "Content-Disposition": (
                        'attachment; filename="review-defense-rgpd-export.json"'
                    )
                },
            )

        if method == "GET" and path == "/v1/privacy/requests":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER")
            scope = parse_qs(environ.get("QUERY_STRING", "")).get("scope", ["self"])[0]
            org_scope = scope == "organization"
            if org_scope:
                self._require_role(user, "OWNER", "ADMIN")
            requester = None if org_scope else user.user_id
            rows = []
            if self.repository is not None and hasattr(self.repository, "list_privacy_requests"):
                rows = [self._privacy_request_payload(r) for r in (self.repository.list_privacy_requests(user.organization_id, requester) or [])]
            if not rows:
                rows = [dict(v) for v in self.store.privacy_requests.values()
                        if v.get("organization_id") == user.organization_id and (org_scope or v.get("requester_user_id") == user.user_id)]
            return self._json(200, {"items": rows, "count": len(rows), "scope": "organization" if org_scope else "self"})

        if method == "PATCH" and path.startswith("/v1/privacy/requests/"):
            self._require_role(user, "OWNER", "ADMIN")
            request_id = path.rsplit("/", 1)[-1]
            body = self._body(environ)
            status = str(body.get("status", "")).upper()
            allowed = {"RECEIVED", "IN_REVIEW", "COMPLETED", "REJECTED"}
            if status not in allowed:
                raise APIError(422, "VALIDATION_ERROR", "invalid privacy request status")
            note = body.get("response_note")
            if note is not None and not isinstance(note, str):
                raise APIError(422, "VALIDATION_ERROR", "response_note must be text")
            row = None
            if self.repository is not None and hasattr(self.repository, "update_privacy_request"):
                persisted = self.repository.update_privacy_request(user.organization_id, request_id, status, note)
                if persisted:
                    row = dict(zip(("id","status","response_note","due_at","created_at","updated_at"), persisted))
            if row is None:
                row = self.store.privacy_requests.get(request_id)
                if row and row.get("organization_id") == user.organization_id:
                    row["status"] = status
                    row["response_note"] = note
                    row["updated_at"] = utc_now().isoformat()
            if row is None:
                raise APIError(404, "NOT_FOUND", "privacy request not found")
            self.store.privacy_requests[request_id] = {**self.store.privacy_requests.get(request_id, {}), **row, "organization_id": user.organization_id}
            self.store.audit_event(user.organization_id, user.user_id, "PRIVACY_REQUEST_UPDATED", f"privacy_request:{request_id}", status=status)
            return self._json(200, {"request": self.store.privacy_requests[request_id]})

        if method == "POST" and path == "/v1/privacy/requests":
            body = self._body(environ)
            request_type = str(body.get("request_type", "")).upper()
            allowed = {"ACCESS", "RECTIFICATION", "ERASURE", "RESTRICTION", "OBJECTION", "PORTABILITY"}
            if request_type not in allowed:
                raise APIError(422, "VALIDATION_ERROR", "invalid privacy request type")
            details = body.get("details") if isinstance(body.get("details"), dict) else {}
            import datetime as _datetime
            created = utc_now()
            due = created + _datetime.timedelta(days=30)
            request_id = str(uuid.uuid4())
            row = {
                "id": request_id,
                "organization_id": user.organization_id,
                "requester_user_id": user.user_id,
                "request_type": request_type,
                "status": "RECEIVED",
                "details": details,
                "response_note": None,
                "due_at": due.isoformat(),
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
            }
            if self.repository is not None and hasattr(self.repository, "create_privacy_request"):
                persisted = self.repository.create_privacy_request(
                    user.organization_id, user.user_id, request_type, details, due.isoformat()
                )
                if persisted:
                    row.update(dict(zip(("id","status","created_at","updated_at","due_at"), persisted)))
                    row["organization_id"] = user.organization_id
                    row["requester_user_id"] = user.user_id
                    row["request_type"] = request_type
                    row["details"] = details
                    row["response_note"] = None
            self.store.privacy_requests[request_id] = row
                        self.store.audit_event(user.organization_id,
                 user.user_id,
                 "PRIVACY_REQUEST_CREATED",
                 f"privacy_request:{row['id']}",
                request_type=request_type)
            return self._json(201, {"request": row})

        if method == "GET" and path == "/v1/privacy/consents":
            rows = []
            if self.repository is not None and hasattr(self.repository, "list_privacy_consents"):
                rows = [dict(zip(("id","purpose","policy_version","granted","granted_at","withdrawn_at"), r))
                        for r in (self.repository.list_privacy_consents(user.organization_id, user.user_id) or [])]
            if not rows:
                rows = [dict(v) for v in self.store.privacy_consents
                        if v.get("organization_id") == user.organization_id and v.get("user_id") == user.user_id]
            return self._json(200, {"items": rows, "count": len(rows)})

        if method == "POST" and path == "/v1/privacy/consents":
            body = self._body(environ)
            purpose = str(body.get("purpose", "")).strip()
            policy_version = str(body.get("policy_version", "")).strip()
            if not purpose or not policy_version:
                raise APIError(422, "VALIDATION_ERROR", "purpose and policy_version are required")
            granted = bool(body.get("granted"))
            row = {
                "id": str(uuid.uuid4()),
                "organization_id": user.organization_id,
                "user_id": user.user_id,
                "purpose": purpose,
                "policy_version": policy_version,
                "granted": granted,
                "granted_at": utc_now().isoformat(),
                "withdrawn_at": None if granted else utc_now().isoformat(),
            }
            if self.repository is not None and hasattr(self.repository, "create_privacy_consent"):
                persisted = self.repository.create_privacy_consent(
                    user.organization_id, user.user_id, purpose, policy_version, granted
                )
                if persisted:
                    row.update(dict(zip(("id","purpose","policy_version","granted","granted_at","withdrawn_at"), persisted)))
                    row["organization_id"] = user.organization_id
                    row["user_id"] = user.user_id
            self.store.privacy_consents.append(row)
                        self.store.audit_event(user.organization_id,
                 user.user_id,
                 "PRIVACY_CONSENT_RECORDED",
                 f"consent:{row['id']}",
                 purpose=purpose,
                 granted=granted,
                policy_version=policy_version)
            return self._json(201, {"consent": row})

        if method == "GET" and path == "/v1/me":
            return self._json(200, {"user_id": user.user_id, "organization_id": user.organization_id, "email": user.email, "role": user.role})
        if method == "POST" and path == "/v1/auth/change-password":
            body = self._body(environ)
            current = body.get("current_password", "")
            new_password = body.get("new_password", "")
            if not isinstance(current, str) or not verify_password(current, user.password_hash):
                raise APIError(401, "AUTH_INVALID", "current password is invalid")
            try:
                new_hash = hash_password(new_password)
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            user = User(user.user_id, user.organization_id, user.email, new_hash, user.role)
            self.store.users[user.user_id] = user
            current_hash = hash_token(environ.get("HTTP_AUTHORIZATION", "")[7:].strip())
            for th, sess in list(self.store.sessions.items()):
                if sess.user_id == user.user_id and sess.organization_id == user.organization_id:
                    self.store.sessions[th] = Session(sess.user_id, sess.organization_id, sess.role, sess.token_hash, sess.expires_at, utc_now())
            # Issue a fresh session after revoking all previous sessions.
            raw, fresh = issue_session(user_id=user.user_id, organization_id=user.organization_id, role=user.role, ttl_seconds=self.session_ttl)
            self.store.sessions[fresh.token_hash] = fresh
            if self.repository is not None:
                if hasattr(self.repository, "revoke_all_sessions"):
                    self.repository.revoke_all_sessions(
                        user.organization_id,
                        user.user_id,
                    )
                if hasattr(self.repository, "update_password"):
                    self.repository.update_password(
                        user.organization_id,
                        user.user_id,
                        new_hash,
                    )
                if hasattr(self.repository, "put_session"):
                    self.repository.put_session(
                        user.organization_id,
                        fresh.token_hash,
                        user.user_id,
                        user.role,
                        fresh.expires_at.isoformat(),
                    )
                if hasattr(self.repository, "security_event"):
                    self.repository.security_event(
                        user.organization_id,
                        user.user_id,
                        "PASSWORD_CHANGED",
                        user.user_id,
                    )
            self.store.audit_event(user.organization_id, user.user_id, "PASSWORD_CHANGED", f"user:{user.user_id}")
            return self._json(200, {"status":"password_changed", "access_token":raw, "token_type":"Bearer", "expires_at":fresh.expires_at.isoformat()})
        if method == "POST" and path == "/v1/auth/rotate":
            old_raw = environ.get("HTTP_AUTHORIZATION", "")[7:].strip()
            old_hash = hash_token(old_raw)
            old = self.store.sessions.get(old_hash)
            if old is None:
                raise APIError(401, "AUTH_INVALID", "invalid session")
            raw, fresh = issue_session(user_id=user.user_id, organization_id=user.organization_id, role=user.role, ttl_seconds=self.session_ttl)
            self.store.sessions[old_hash] = Session(old.user_id, old.organization_id, old.role, old.token_hash, old.expires_at, utc_now())
            self.store.sessions[fresh.token_hash] = fresh
            if self.repository is not None:
                self.repository.revoke_session(user.organization_id, old_hash)
                self.repository.put_session(user.organization_id, fresh.token_hash, user.user_id, user.role, fresh.expires_at.isoformat())
            self.store.audit_event(user.organization_id, user.user_id, "SESSION_ROTATED", "session")
            return self._json(200, {"access_token":raw, "token_type":"Bearer", "expires_at":fresh.expires_at.isoformat()})
        if method == "POST" and path == "/v1/auth/revoke-all":
            self._require_role(user, "OWNER", "ADMIN")
            target = self._persistent_uuid(self._body(environ).get("user_id", user.user_id), "user_id")
            target_user = self._user_for_organization(user.organization_id, target)
            if target_user is None:
                raise APIError(404, "NOT_FOUND", "user not found")
            for th, sess in list(self.store.sessions.items()):
                if sess.user_id == target and sess.organization_id == user.organization_id:
                    self.store.sessions[th] = Session(sess.user_id, sess.organization_id, sess.role, sess.token_hash, sess.expires_at, utc_now())
            if self.repository is not None and hasattr(self.repository, "revoke_all_sessions"):
                self.repository.revoke_all_sessions(user.organization_id, target)
                if hasattr(self.repository, "security_event"):
                    self.repository.security_event(user.organization_id, user.user_id, "SESSIONS_REVOKED", target, {})
            self.store.audit_event(user.organization_id, user.user_id, "SESSIONS_REVOKED", f"user:{target}", target_user_id=target)
            return self._json(200, {"status":"sessions_revoked", "user_id":target})
        # ORGANISATION : invitations, membres, rôles et calendrier SLA.
        if method == "POST" and path == "/v1/organization/invitations":
            self._require_role(user, "OWNER", "ADMIN")
            body = self._body(environ)
            try:
                email = normalize_email(str(body.get("email", "")))
                role = validate_role(str(body.get("role", "CLIENT")))
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            if role == "OWNER" and user.role != "OWNER":
                raise APIError(403, "FORBIDDEN", "only an owner can invite an owner")
            from datetime import timedelta
            ttl = int(body.get("ttl_seconds", 7*24*3600))
            if ttl < 300 or ttl > 30*24*3600:
                raise APIError(422, "VALIDATION_ERROR", "invalid invitation ttl")
            token = secrets.token_urlsafe(32)
            token_hash = hash_token(token)
            expires = utc_now() + timedelta(seconds=ttl)
            iid=str(uuid.uuid4())
                        row={"invitation_id":iid,
                "organization_id":user.organization_id,
                "email":email,
                "role":role,
                "expires_at":expires.isoformat(),
                "invited_by":user.user_id,
                "accepted_at":None,
                "revoked_at":None,
                "token_hash":token_hash}
            self.store.invitations[iid]=row
            if self.repository is not None and hasattr(self.repository, "create_invitation"):
                self.repository.create_invitation(user.organization_id,email,role,token_hash,user.user_id,expires.isoformat())
            self.store.audit_event(user.organization_id,user.user_id,"INVITATION_CREATED",f"invitation:{iid}",email=email,role=role)
            # Token is returned once to the caller; it is never persisted in clear text.
            return self._json(201,{k:v for k,v in row.items() if k != "token"}|{"invitation_token":token})
        if method == "GET" and path == "/v1/organization/members":
            if self.repository is not None and hasattr(self.repository, "list_members"):
                rows = [
                    {"user_id": str(uid), "email": str(email), "role": str(role)}
                    for uid, email, role in (self.repository.list_members(user.organization_id) or [])
                ]
            else:
                rows = [{"user_id":u.user_id,"email":u.email,"role":u.role} for u in self.store.users.values() if u.organization_id==user.organization_id]
            return self._json(200,{"items":rows,"count":len(rows)})
        if method == "POST" and path.startswith("/v1/organization/members/") and path.endswith("/role"):
            self._require_role(user,"OWNER","ADMIN")
            target_id=self._persistent_uuid(path.split("/")[4], "user_id")
            body=self._body(environ)
            role=validate_role(str(body.get("role","")))
            target=self._user_for_organization(user.organization_id, target_id)
            if target is None:
                raise APIError(404,"NOT_FOUND","user not found")
            if target.user_id == user.user_id:
                raise APIError(403,"FORBIDDEN","users cannot change their own role")
            if role=="OWNER" and user.role!="OWNER":
                raise APIError(403,"FORBIDDEN","only an owner can assign owner")
            if target.role=="OWNER" and role!="OWNER" and user.role!="OWNER":
                raise APIError(403,"FORBIDDEN","only an owner can demote an owner")
            target=User(target.user_id,target.organization_id,target.email,target.password_hash,role)
            self.store.users[target.user_id]=target
            for token_hash, session in list(self.store.sessions.items()):
                if (
                    session.user_id == target.user_id
                    and session.organization_id == user.organization_id
                ):
                    self.store.sessions[token_hash] = Session(
                        session.user_id,
                        session.organization_id,
                        role,
                        session.token_hash,
                        session.expires_at,
                        utc_now(),
                    )
            if self.repository is not None and hasattr(self.repository,"update_role"):
                self.repository.update_role(user.organization_id,target.user_id,role)
                if hasattr(self.repository,"revoke_all_sessions"):
                    self.repository.revoke_all_sessions(user.organization_id,target.user_id)
            self.store.audit_event(user.organization_id,user.user_id,"ROLE_CHANGED",f"user:{target.user_id}",role=role)
            return self._json(200,{"user_id":target.user_id,"role":role})
        if method == "GET" and path == "/v1/organization/sla-calendar":
            default_calendar = {
                "timezone": "UTC",
                "workdays": [0, 1, 2, 3, 4, 5, 6],
                "start_hour": 0,
                "end_hour": 24,
                "holidays": [],
            }
            return self._json(
                200,
                {
                    "calendar": self.store.sla_calendars.get(
                        user.organization_id,
                        default_calendar,
                    ),
                    "business_calendar_configured": (
                        user.organization_id in self.store.sla_calendars
                    ),
                },
            )
        if method == "POST" and path == "/v1/organization/sla-calendar":
            self._require_role(user, "OWNER", "ADMIN")
            body = self._body(environ)
            try:
                cal = calendar_from_dict(body)
            except (TypeError, ValueError) as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            payload = {
                "timezone": cal.timezone,
                "workdays": list(cal.workdays),
                "start_hour": cal.start_hour,
                "end_hour": cal.end_hour,
                "holidays": list(cal.holidays),
            }
            self.store.sla_calendars[user.organization_id] = payload
            if self.repository is not None and hasattr(self.repository, "upsert_sla_calendar"):
                self.repository.upsert_sla_calendar(user.organization_id, payload)
            self.store.audit_event(user.organization_id, user.user_id, "SLA_CALENDAR_UPDATED", f"organization:{user.organization_id}", calendar=payload)
            return self._json(200, {"calendar":payload})
        # AVIS ET PREUVES : avis, pièces jointes et vérification des éléments.
        if method == "POST" and path == "/v1/reviews":
            body = self._body(environ)
            rid = str(body.get("review_id", ""))
            if not rid or not str(body.get("text", "")).strip():
                raise APIError(422, "VALIDATION_ERROR", "review_id and text are required")
            try:
                rating = int(body.get("rating", 0))
            except Exception as exc:
                raise APIError(422, "VALIDATION_ERROR", "rating must be an integer") from exc
            if rating < 1 or rating > 5:
                raise APIError(422, "VALIDATION_ERROR", "rating must be between 1 and 5")
            review = ReviewContext(
                rid,
                user.organization_id,
                str(body.get("location_id", "")),
                body.get("author_display_name"),
                rating,
                str(body["text"]),
                str(body.get("published_at", "")),
                body.get("updated_at"),
                body.get("language"),
                "GOOGLE",
                body.get("review_url"),
            )
            key = (user.organization_id, rid)
            self.store.reviews[key] = review
            if self.repository is not None:
                self.repository.upsert_review(user.organization_id, asdict(review))
            self.store.audit_event(user.organization_id, user.user_id, "REVIEW_INGESTED", f"review:{rid}")
            return self._json(201, {"review": asdict(review)})
        if method == "GET" and path == "/v1/reviews":
            rows = [r for (org, _), r in self.store.reviews.items() if org == user.organization_id]
            if self.repository is not None and hasattr(self.repository, "list_reviews"):
                for row in self.repository.list_reviews(user.organization_id):
                    review = _review_from_row(row)
                    self.store.reviews[(user.organization_id, review.review_id)] = review
                rows = [r for (org, _), r in self.store.reviews.items() if org == user.organization_id]
            return self._json(200, {"items": [asdict(r) for r in rows], "count": len(rows)})
        if method == "GET" and path.startswith("/v1/reviews/"):
            rid = path.rsplit("/", 1)[-1]
            review = self.store.reviews.get((user.organization_id, rid))
            if review is None and self.repository is not None and hasattr(self.repository, "get_review"):
                row = self.repository.get_review(user.organization_id, rid)
                if row:
                    review = _review_from_row(row)
                    self.store.reviews[(user.organization_id, rid)] = review
            if not review:
                raise APIError(404, "NOT_FOUND", "review not found")
            claims = extract_claims(review)
            signals = classify_policy_signals(claims)
            return self._json(200, {"review": asdict(review), "claims": [asdict(c) for c in claims], "policy_signals": [asdict(s) for s in signals]})
        if method == "POST" and path == "/v1/evidence":
            body = self._body(environ)
            case_id = self._persistent_uuid(body.get("case_id", ""), "case_id")
            case_key = (user.organization_id, case_id)
            if case_key not in self.store.cases and self.repository is not None and hasattr(self.repository, "get_case_persistent"):
                row = self.repository.get_case_persistent(user.organization_id, case_id)
                if row:
                    self.store.cases[case_key] = CaseService.from_row(row)
            if case_key not in self.store.cases:
                raise APIError(404, "NOT_FOUND", "case not found")
            filename = str(body.get("filename", ""))
            content_type = str(body.get("content_type", ""))
            encoded = body.get("content_base64")
            if not filename or not isinstance(encoded, str):
                raise APIError(422, "VALIDATION_ERROR", "filename and content_base64 are required")
            try:
                content = base64.b64decode(encoded, validate=True)
            except Exception as exc:
                raise APIError(422, "VALIDATION_ERROR", "content_base64 is invalid") from exc
            evidence_id = str(uuid.uuid4())
            try:
                obj = self.store.vault.put(
                    organization_id=user.organization_id,
                    evidence_id=evidence_id,
                    content=content,
                    content_type=content_type,
                    filename=filename,
                )
            except (ValueError, PermissionError) as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            raw_facts = body.get("facts", [])
            if raw_facts is None:
                raw_facts = []
            if not isinstance(raw_facts, list) or any(not isinstance(f, dict) for f in raw_facts):
                raise APIError(422, "VALIDATION_ERROR", "facts must be a list of objects")
            facts = []
            for f in raw_facts:
                key, kind, value = str(f.get("key", "")), str(f.get("kind", "")), str(f.get("value", ""))
                if not key or not kind or not value or len(key) > 200 or len(kind) > 80 or len(value) > 5000:
                    raise APIError(422, "VALIDATION_ERROR", "each fact requires bounded key, kind and value")
                facts.append({
                    "fact_id": str(uuid.uuid4()),
                    "evidence_id": evidence_id,
                    "case_id": case_id,
                    "organization_id": user.organization_id,
                    "key": key,
                    "kind": kind,
                    "value": value,
                    "source_location": str(f.get("source_location", "")),
                    "verified": False,
                    "verified_by": None,
                    "verified_at": None,
                })
            extracted_text = ""
            extraction_method = "not-run"
            if not facts and content_type.lower().split(";", 1)[0].strip() in {
                "text/plain",
                "text/csv",
                "application/json",
                "application/pdf",
                "image/jpeg",
                "image/png",
                "image/webp",
            }:
                try:
                    extracted = extract_readable_text(content=content, content_type=content_type, filename=filename)
                    extracted_text = extracted.text
                    extraction_method = extracted.method
                    suggested = extract_text_fact_suggestions(evidence_id=evidence_id, content=extracted_text.encode("utf-8"), content_type="text/plain")
                    for suggestion in suggested:
                        facts.append({
                            # The extraction engine's public suggestion IDs are prefixed strings;
                            # evidence_facts.fact_id is a PostgreSQL UUID column.
                            "fact_id": str(uuid.uuid5(
                                uuid.NAMESPACE_URL,
                                f"review-defense:evidence:{evidence_id}:suggestion:{suggestion.suggestion_id}",
                            )),
                            "evidence_id": evidence_id,
                            "case_id": case_id,
                            "organization_id": user.organization_id,
                            "key": suggestion.key,
                            "kind": suggestion.kind,
                            "value": suggestion.value,
                            "source_location": suggestion.source_location,
                            "verified": False,
                            "verified_by": None,
                            "verified_at": None,
                        })
                except ExtractionError:
                    extraction_method = "failed"
            row = {
                "evidence_id": evidence_id,
                "organization_id": user.organization_id,
                "case_id": case_id,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": obj.size_bytes,
                "sha256": obj.sha256,
                "object_key": obj.object_key,
                "verified": False,
                "status": "PENDING",
                "created_by": user.user_id,
                "extraction_method": extraction_method,
                "extracted_chars": len(extracted_text),
            }
            self.store.evidence[(user.organization_id, evidence_id)] = row
            self.store.evidence_facts[(user.organization_id, evidence_id)] = facts
            if self.repository is not None:
                self.repository.put_evidence(user.organization_id, row)
                for fact in facts:
                    self.repository.put_evidence_fact(user.organization_id, fact)
            self.store.audit_event(user.organization_id, user.user_id, "EVIDENCE_UPLOADED", f"evidence:{evidence_id}", sha256=obj.sha256, case_id=case_id)
            row = dict(row)
            row["download_url"] = sign_download_url(
                object_key=obj.object_key,
                organization_id=user.organization_id,
                secret=self.store.download_secret,
            )
            return self._json(201, {"evidence": row})
        if method == "GET" and path == "/v1/evidence":
            rows = [
                {
                    **evidence,
                    "status": (
                        "VERIFIED" if evidence.get("verified") else "PENDING"
                    ),
                }
                for (organization_id, _), evidence in self.store.evidence.items()
                if organization_id == user.organization_id
            ]
            return self._json(200, {"items": rows, "count": len(rows)})
        if method == "GET" and path.startswith("/v1/evidence/") and path.endswith("/content") and len(path.split("/")) == 5:
            eid = path.split("/")[3]
            row = self.store.evidence.get((user.organization_id, eid))
            if row is None and self.repository is not None and hasattr(self.repository, "get_evidence"):
                dbrow = self.repository.get_evidence(user.organization_id, eid)
                if dbrow:
                    row = dict(zip(
                        (
                            "evidence_id",
                            "organization_id",
                            "case_id",
                            "filename",
                            "content_type",
                            "size_bytes",
                            "sha256",
                            "object_key",
                            "verified",
                            "created_by",
                            "verified_by",
                            "verified_at",
                        ),
                        dbrow,
                    ))
                    self.store.evidence[(user.organization_id, eid)] = row
            if not row:
                raise APIError(404, "NOT_FOUND", "evidence not found")
            content = self.store.vault.get(organization_id=user.organization_id, object_key=row["object_key"])
            if not verify_integrity(content, row["sha256"]):
                raise APIError(409, "INTEGRITY_FAILURE", "stored evidence integrity check failed")
            return self._json(200, {
                "filename": row["filename"],
                "content_type": row["content_type"],
                "content_base64": base64.b64encode(content).decode("ascii"),
                "sha256": row["sha256"],
            })
        if method == "GET" and path.startswith("/v1/evidence/"):
            eid = path.rsplit("/", 1)[-1]
            row = self.store.evidence.get((user.organization_id, eid))
            if row is None and self.repository is not None and hasattr(self.repository, "get_evidence"):
                dbrow = self.repository.get_evidence(user.organization_id, eid)
                if dbrow:
                    row = dict(zip(
                        (
                            "evidence_id",
                            "organization_id",
                            "case_id",
                            "filename",
                            "content_type",
                            "size_bytes",
                            "sha256",
                            "object_key",
                            "verified",
                            "created_by",
                            "verified_by",
                            "verified_at",
                        ),
                        dbrow,
                    ))
                    self.store.evidence[(user.organization_id, eid)] = row
            if not row:
                raise APIError(404, "NOT_FOUND", "evidence not found")
            if not verify_integrity(self.store.vault.get(organization_id=user.organization_id, object_key=row["object_key"]), row["sha256"]):
                raise APIError(409, "INTEGRITY_FAILURE", "stored evidence integrity check failed")
            out = dict(row)
            out["status"] = "VERIFIED" if row.get("verified") else "PENDING"
            return self._json(200, {"evidence": out})
        if method == "POST" and path.startswith("/v1/evidence/") and path.endswith("/verify") and len(path.split("/")) == 5:
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            eid = path.split("/")[3]
            row = self.store.evidence.get((user.organization_id, eid))
            if row is None and self.repository is not None and hasattr(self.repository, "get_evidence"):
                dbrow = self.repository.get_evidence(user.organization_id, eid)
                if dbrow:
                    row = dict(zip(
                        (
                            "evidence_id",
                            "organization_id",
                            "case_id",
                            "filename",
                            "content_type",
                            "size_bytes",
                            "sha256",
                            "object_key",
                            "verified",
                            "created_by",
                            "verified_by",
                            "verified_at",
                        ),
                        dbrow,
                    ))
                    self.store.evidence[(user.organization_id, eid)] = row
            if not row:
                raise APIError(404, "NOT_FOUND", "evidence not found")
            if not verify_integrity(self.store.vault.get(organization_id=user.organization_id, object_key=row["object_key"]), row["sha256"]):
                raise APIError(409, "INTEGRITY_FAILURE", "stored evidence integrity check failed")
            row["verified"] = True
            row["status"] = "VERIFIED"
            row["verified_by"] = user.user_id
            row["verified_at"] = utc_now().isoformat()
            if self.repository is not None and hasattr(self.repository, "update_evidence_verification"):
                self.repository.update_evidence_verification(user.organization_id, eid, user.user_id, row["verified_at"])
            self.store.audit_event(user.organization_id, user.user_id, "EVIDENCE_VERIFIED", f"evidence:{eid}")
            return self._json(200, {"evidence": row})
        if method == "POST" and path.startswith("/v1/evidence/") and path.endswith("/facts/verify"):
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            eid = path.split("/")[3]
            key = (user.organization_id, eid)
            row = self.store.evidence.get(key)
            # Production uses multiple workers. A verification request can land
            # on a worker whose in-memory cache still contains the pre-verification
            # row. Always reconcile the evidence state from PostgreSQL first when
            # persistence is available so the facts gate observes the durable state.
            if self.repository is not None and hasattr(self.repository, "get_evidence"):
                dbrow = self.repository.get_evidence(user.organization_id, eid)
                if dbrow:
                    row = dict(zip(
                        (
                            "evidence_id",
                            "organization_id",
                            "case_id",
                            "filename",
                            "content_type",
                            "size_bytes",
                            "sha256",
                            "object_key",
                            "verified",
                            "created_by",
                            "verified_by",
                            "verified_at",
                        ),
                        dbrow,
                    ))
                    self.store.evidence[key] = row
            if not row:
                raise APIError(404, "NOT_FOUND", "evidence not found")
            if not row.get("verified"):
                raise APIError(409, "STATE_CONFLICT", "evidence must be verified before its facts can be verified")
            body = self._body(environ)
            fact_ids = body.get("fact_ids")
            facts = self.store.evidence_facts.get(key, [])
            if self.repository is not None and hasattr(self.repository, "list_evidence_facts"):
                dbfacts = self.repository.list_evidence_facts(user.organization_id, row["case_id"])
                facts = [
                    {
                        "fact_id": str(r[0]), "evidence_id": str(r[1]), "case_id": str(r[2]),
                        "key": str(r[3]), "kind": str(r[4]), "value": str(r[5]),
                        "source_location": str(r[6] or ""), "verified": bool(r[7]),
                        "verified_by": str(r[8]) if r[8] is not None else None,
                        "verified_at": _iso_value(r[9]),
                    }
                    for r in dbfacts if str(r[1]) == eid
                ]
                self.store.evidence_facts[key] = facts
            if fact_ids is None:
                fact_ids = [f["fact_id"] for f in facts]
            if not isinstance(fact_ids, list):
                raise APIError(422, "VALIDATION_ERROR", "fact_ids must be a list")
            selected = set(str(x) for x in fact_ids)
            changed = 0
            for fact in facts:
                if fact["fact_id"] in selected:
                    fact["verified"] = True
                    fact["verified_by"] = user.user_id
                    fact["verified_at"] = utc_now().isoformat()
                    changed += 1
            if self.repository is not None:
                for fact in facts:
                    self.repository.put_evidence_fact(user.organization_id, fact)
                        self.store.audit_event(user.organization_id,
                 user.user_id,
                 "EVIDENCE_FACTS_VERIFIED",
                 f"evidence:{eid}",
                 fact_ids=sorted(selected),
                count=changed)
            return self._json(200, {"facts": facts, "verified_count": changed})
        # PILOTAGE : file de traitement, affectations, escalades et notifications.
        if method == "GET" and path == "/v1/review-queue":
            items = []
            for (org, cid), case in self.store.cases.items():
                if org != user.organization_id:
                    continue
                review = self.store.reviews.get((org, case.review_id))
                if review is None:
                    continue
                claims = extract_claims(review)
                signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get((org, cid), [])
                suggestions = self.store.fact_suggestions.get((org, cid), [])
                evidence_rows = [e for (eo, _), e in self.store.evidence.items() if eo == org and e.get("case_id") == cid]
                                evidence = tuple(EvidenceView(e["evidence_id"],
                     e["filename"],
                     e.get("content_type") or "UNKNOWN",
                     e["sha256"],
                    "VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws = CaseWorkspace(cid, org, case.status, "NORMAL", ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
                    tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims),
                    tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals), evidence, (),
                    tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions))
                required = {c.claim_id: [] for c in claims}
                missing = missing_evidence_tasks(ws, required)
                                item = score_case(case_id=cid,
                     created_at=case.created_at,
                     policy_statuses=[s.status for s in signals],
                     contradiction_count=len(contradictions),
                     missing_evidence_count=len(missing),
                     unverified_suggestion_count=len([x for x in suggestions if not x.get("verified")]),
                    assigned_to=case.assigned_to)
                payload = asdict(item)
                payload["sla"] = asdict(self.case_sla.calculate(case, item.priority, self._calendar(user.organization_id)))
                items.append(payload)
            items.sort(key=lambda x: (-x["priority_score"], x["assigned_to"] is not None, x["case_id"]))
            return self._json(200, {"items": items, "count": len(items)})
        if method == "GET" and path == "/v1/review-queue/workload":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            rows: dict[str, dict[str, Any]] = {}
            for (org, cid), case in self.store.cases.items():
                if org != user.organization_id:
                    continue
                review = self.store.reviews.get((org, case.review_id))
                if review is None:
                    continue
                claims = extract_claims(review)
                signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get((org, cid), [])
                suggestions = self.store.fact_suggestions.get((org, cid), [])
                evidence_rows = [e for (eo, _), e in self.store.evidence.items() if eo == org and e.get("case_id") == cid]
                                evidence = tuple(EvidenceView(e["evidence_id"],
                     e["filename"],
                     e.get("content_type") or "UNKNOWN",
                     e["sha256"],
                    "VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws = CaseWorkspace(cid, org, case.status, "NORMAL", ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
                    tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims),
                    tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals), evidence, (),
                    tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions))
                missing = missing_evidence_tasks(ws, {c.claim_id: [] for c in claims})
                                item = score_case(case_id=cid,
                     created_at=case.created_at,
                     policy_statuses=[s.status for s in signals],
                     contradiction_count=len(contradictions),
                     missing_evidence_count=len(missing),
                     unverified_suggestion_count=len([x for x in suggestions if not x.get("verified")]),
                    assigned_to=case.assigned_to)
                key = case.assigned_to or "UNASSIGNED"
                row = rows.setdefault(key,
                     {"user_id": case.assigned_to,
                     "case_count": 0,
                     "priority_score_total": 0,
                     "critical_count": 0,
                     "high_count": 0,
                     "overdue_count": 0,
                    "due_soon_count": 0})
                row["case_count"] += 1
                row["priority_score_total"] += item.priority_score
                if item.priority == "CRITICAL":
                    row["critical_count"] += 1
                elif item.priority == "HIGH":
                    row["high_count"] += 1
                sla = self.case_sla.calculate(case, item.priority, self._calendar(user.organization_id))
                if sla.status == "OVERDUE":
                    row["overdue_count"] += 1
                elif sla.status == "DUE_SOON":
                    row["due_soon_count"] += 1
            items = sorted(rows.values(), key=lambda x: (-x["overdue_count"], -x["priority_score_total"], str(x["user_id"])))
            return self._json(200, {"items": items, "count": len(items)})
        if method == "POST" and path.startswith("/v1/review-queue/") and path.endswith("/claim"):
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            cid = path.split("/")[3]
            case = self.store.cases.get((user.organization_id, cid))
            if not case:
                raise APIError(404, "NOT_FOUND", "case not found")
            if case.assigned_to and case.assigned_to != user.user_id:
                raise APIError(409, "ALREADY_ASSIGNED", "case is already assigned")
            self.case_operations.assign(case=case, user_id=user.user_id)
            return self._json(200, {"case_id": cid, "assigned_to": user.user_id})
        if method == "POST" and path.startswith("/v1/review-queue/") and path.endswith("/unclaim"):
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            cid = path.split("/")[3]
            case = self.store.cases.get((user.organization_id, cid))
            if not case:
                raise APIError(404, "NOT_FOUND", "case not found")
            if case.assigned_to not in (None, user.user_id) and user.role not in {"OWNER", "ADMIN"}:
                raise APIError(403, "FORBIDDEN", "only the assignee or manager may unclaim")
            self.case_operations.unassign(case=case, user_id=user.user_id)
            return self._json(200, {"case_id": cid, "assigned_to": None})
        if method == "GET" and path == "/v1/escalations":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            items = self.case_escalations.list_for_organization(
                organization_id=user.organization_id,
                calendar=self._calendar(user.organization_id),
            )
            return self._json(200, {"items": items, "count": len(items)})
        if method == "POST" and path.startswith("/v1/escalations/") and path.endswith("/acknowledge"):
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            parts = path.split("/")
            cid = parts[3]
            level = str(self._body(environ).get("level", "DUE"))
            esc = self.store.escalations.get((user.organization_id, cid, level))
            if esc is None:
                raise APIError(404, "NOT_FOUND", "escalation not found")
            if esc.status == "RESOLVED":
                raise APIError(409, "STATE_CONFLICT", "escalation is already resolved")
            try:
                esc = self.case_escalations.acknowledge(
                    organization_id=user.organization_id,
                    case_id=cid,
                    level=level,
                    user_id=user.user_id,
                )
            except KeyError as exc:
                raise APIError(404, "NOT_FOUND", "escalation not found") from exc
            except ValueError as exc:
                raise APIError(409, "STATE_CONFLICT", str(exc)) from exc
            return self._json(200, {"escalation": esc.payload()})
        if method == "POST" and path.startswith("/v1/escalations/") and path.endswith("/resolve"):
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            parts = path.split("/")
            cid = parts[3]
            level = str(self._body(environ).get("level", "DUE"))
            esc = self.store.escalations.get((user.organization_id, cid, level))
            if esc is None:
                raise APIError(404, "NOT_FOUND", "escalation not found")
            if esc.status == "RESOLVED":
                raise APIError(409, "STATE_CONFLICT", "escalation is already resolved")
            try:
                esc = self.case_escalations.resolve(
                    organization_id=user.organization_id,
                    case_id=cid,
                    level=level,
                    user_id=user.user_id,
                )
            except KeyError as exc:
                raise APIError(404, "NOT_FOUND", "escalation not found") from exc
            except ValueError as exc:
                raise APIError(409, "STATE_CONFLICT", str(exc)) from exc
            return self._json(200, {"escalation": esc.payload()})
        if method == "GET" and path == "/v1/organization/notification-policy":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            policy, configured = self.notifications.policy_for_organization(organization_id=user.organization_id)
            return self._json(200, {"policy": policy.payload(), "configured": configured})
        if method == "POST" and path == "/v1/organization/notification-policy":
            self._require_role(user, "OWNER", "ADMIN")
            try:
                policy = self.notifications.set_policy(organization_id=user.organization_id,
                                                       payload=self._body(environ), actor_id=user.user_id)
            except ValueError as exc:
                raise APIError(400, "INVALID_NOTIFICATION_POLICY", str(exc))
            return self._json(200, {"policy": policy.payload()})
        if method == "POST" and path == "/v1/notifications/worker/run":
            self._require_role(user, "OWNER", "ADMIN")
            body = self._body(environ)
            try:
                limit = int(body.get("limit", 25))
            except (TypeError, ValueError):
                raise APIError(400, "INVALID_LIMIT", "limit must be an integer")
            try:
                result = self.notifications.run_worker(organization_id=user.organization_id,
                                                        limit=limit, actor_id=user.user_id)
            except ValueError as exc:
                raise APIError(400, "INVALID_LIMIT", str(exc))
            return self._json(200, {"result": asdict(result)})
        if method == "GET" and path == "/v1/notifications":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            status_filter = parse_qs(environ.get("QUERY_STRING", "")).get("status", [None])[0]
            items = self.notifications.list_for_organization(organization_id=user.organization_id,
                                                              status=status_filter)
            return self._json(200, {"items": items, "count": len(items)})
        if method == "GET" and path == "/v1/notifications/metrics":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            metrics = self.notifications.metrics_for_organization(organization_id=user.organization_id)
            return self._json(200, {"metrics": metrics})
        if method == "POST" and path.startswith("/v1/escalations/") and path.endswith("/notify"):
            self._require_role(user, "OWNER", "ADMIN")
            parts = path.split("/")
            cid = parts[3]
            body = self._body(environ)
            level = str(body.get("level", "DUE"))
            channel = str(body.get("channel", "IN_APP"))
            target = str(body.get("target", user.user_id))
            try:
                n, dedup = self.case_escalations.queue_notification(
                    notifications=self.notifications,
                    organization_id=user.organization_id,
                    case_id=cid,
                    level=level,
                    channel=channel,
                    target=target,
                    subject=str(body.get("subject", f"Review Defense escalation: {level}")),
                    body=str(body.get("body") or f"Review Defense escalation {level} for case {cid}."),
                    actor_id=user.user_id,
                )
            except KeyError as exc:
                raise APIError(404, "NOT_FOUND", "escalation not found") from exc
            except ValueError as exc:
                raise APIError(409, "STATE_CONFLICT", str(exc)) from exc
            except PermissionError as exc:
                raise APIError(403, "NOTIFICATION_POLICY_BLOCKED", str(exc)) from exc
            return self._json(200 if dedup else 201, {"notification": n.payload(), "deduplicated": dedup})
        if method == "POST" and path.startswith("/v1/notifications/") and path.endswith("/cancel"):
            self._require_role(user,"OWNER","ADMIN")
            nid=path.split("/")[3]
            try:
                n=self.notifications.cancel(organization_id=user.organization_id,notification_id=nid,actor_id=user.user_id)
            except KeyError as exc:
                raise APIError(404,"NOT_FOUND","notification not found") from exc
            except ValueError as exc:
                raise APIError(409,"STATE_CONFLICT",str(exc)) from exc
            return self._json(200,{"notification":n.payload()})
        if method == "POST" and path.startswith("/v1/notifications/") and path.endswith("/deliver"):
            self._require_role(user,"OWNER","ADMIN")
            nid=path.split("/")[3]
            try:
                n,result=self.notifications.deliver(organization_id=user.organization_id,notification_id=nid,actor_id=user.user_id)
            except KeyError as exc:
                raise APIError(404,"NOT_FOUND","notification not found") from exc
            except PermissionError as exc:
                raise APIError(403,"NOTIFICATION_POLICY_BLOCKED",str(exc)) from exc
            except DeliveryError as exc:
                try:
                    current=self.notifications._get(organization_id=user.organization_id,notification_id=nid)
                except KeyError as missing:
                    raise APIError(404,"NOT_FOUND","notification not found") from missing
                return self._json(502,{"error":{"code":"DELIVERY_FAILED","message":str(exc)},"notification":current.payload()})
            return self._json(200,{"notification":n.payload(),"delivery":result.__dict__})
        if method == "POST" and path.startswith("/v1/notifications/") and path.endswith("/mark-sent"):
            self._require_role(user,"OWNER","ADMIN")
            nid=path.split("/")[3]
            try:
                n=self.notifications.mark_sent(organization_id=user.organization_id,notification_id=nid,actor_id=user.user_id)
            except KeyError as exc:
                raise APIError(404,"NOT_FOUND","notification not found") from exc
            except ValueError as exc:
                raise APIError(409,"STATE_CONFLICT",str(exc)) from exc
            return self._json(200,{"notification":n.payload()})
        # DOSSIERS : validations humaines, soumissions et cycle de vie.
        if method == "GET" and path == "/v1/approvals":
            self._require_role(user, "OWNER", "ADMIN")
            rows = self.case_approvals.list_for_organization(organization_id=user.organization_id)
            return self._json(200, {"items": rows, "count": len(rows)})
        if method == "GET" and path == "/v1/submissions":
            self._require_role(user, "OWNER", "ADMIN")
            rows = self.case_submissions.list_for_organization(
                organization_id=user.organization_id,
            )
            return self._json(200, {"items": rows, "count": len(rows)})
        if method == "POST" and path == "/v1/cases":
            self._require_role(user, "CLIENT", "OWNER", "ADMIN", "ANALYST")
            self.case_lifecycle.repository = self.repository
            body = self._body(environ)
            rid = str(body.get("review_id", ""))
            if (user.organization_id, rid) not in self.store.reviews and self.repository is not None and hasattr(self.repository, "get_review"):
                row = self.repository.get_review(user.organization_id, rid)
                if row:
                    review = _review_from_row(row)
                    self.store.reviews[(user.organization_id, rid)] = review
            if (user.organization_id, rid) not in self.store.reviews:
                raise APIError(404, "NOT_FOUND", "review not found")
            def create():
                case = self.case_lifecycle.create(
                    organization_id=user.organization_id,
                    review_id=rid,
                    actor_id=user.user_id,
                )
                return {"case": asdict(case)}
            return self._json(201, self._idem(user, environ, body, create))
        if method == "GET" and path == "/v1/cases":
            self.case_lifecycle.repository = self.repository
            rows = self.case_lifecycle.list_for_organization(
                organization_id=user.organization_id,
            )
            return self._json(200, {"items": [asdict(c) for c in rows], "count": len(rows)})
        if path.startswith("/v1/cases/"):
            parts = path.split("/")
            if len(parts) < 4:
                raise APIError(404, "NOT_FOUND", "resource not found")
            cid = parts[3]
            case, _review, _evidence, _evidence_facts = CaseService.hydrate_context(
                self.store, self.repository, user.organization_id, cid, _review_from_row
            )
            if not case:
                raise APIError(404, "NOT_FOUND", "case not found")
            if method == "GET" and len(parts) == 4:
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review)
                signals = classify_policy_signals(claims)
                                return self._json(200,
                     {"case": asdict(case),
                     "review": asdict(review),
                     "claims": [asdict(c) for c in claims],
                    "policy_signals": [asdict(s) for s in signals]})
            if method == "GET" and len(parts) == 5 and parts[4] == "history":
                events = []
                if self.repository is not None and hasattr(self.repository, "list_case_events"):
                    events = self.repository.list_case_events(user.organization_id, cid)
                if not events:
                    events = [
                        {
                            "event_id": e["event_id"],
                            "event_type": e["action"],
                            "actor_user_id": e.get("actor_id"),
                            "payload": e.get("meta", {}),
                            "created_at": e["at"],
                        }
                        for e in self.store.audit
                        if e["organization_id"] == user.organization_id
                        and (e["resource"] == f"case:{cid}" or e.get("meta", {}).get("case_id") == cid)
                    ]
                return self._json(200, {"case_id": cid, "items": events, "count": len(events)})

            if method == "GET" and len(parts) == 5 and parts[4] == "workspace":
                review = self.store.reviews[(user.organization_id, case.review_id)]
                evidence_rows = [
                    e for e in self.store.evidence.values()
                    if e.get("organization_id") == user.organization_id and e.get("case_id") == cid
                ]
                audit_rows = [
                    a for a in self.store.audit
                    if a["organization_id"] == user.organization_id
                    and (a["resource"] == f"case:{cid}" or a["resource"].startswith("evidence:")
                         and a.get("meta", {}).get("case_id") == cid)
                ]
                stored_contradictions = self.store.contradictions.get((user.organization_id, cid), [])
                workspace, tasks = CaseWorkspaceService.build(
                    case, review, evidence_rows, audit_rows, stored_contradictions
                )
                review_payload = asdict(workspace.review)
                review_payload.update(
                    {
                        "author_display_name": review.author_display_name,
                        "source": review.source,
                        "language": review.language,
                        "review_url": review.review_url,
                    }
                )
                decision = (
                    self.store.decisions.get(
                        (user.organization_id, case.decision_id)
                    )
                    if case.decision_id
                    else None
                )
                snapshot = self.store.snapshots.get(
                    (user.organization_id, cid)
                )
                approvals = [
                    asdict(approval)
                    for approval in self.store.approvals
                    if approval.organization_id == user.organization_id
                    and approval.decision_id == case.decision_id
                ]
                fact_suggestions = [
                    suggestion
                    for (organization_id, _), suggestions in (
                        self.store.fact_suggestions.items()
                    )
                    if organization_id == user.organization_id
                    for suggestion in suggestions
                    if self.store.evidence.get(
                        (organization_id, suggestion["evidence_id"]),
                        {},
                    ).get("case_id") == cid
                ]
                return self._json(
                    200,
                    {
                        "workspace": {
                            **asdict(workspace),
                            "review": review_payload,
                        },
                        "evidence_tasks": [asdict(task) for task in tasks],
                        "requires_human_review": case_requires_human_review(
                            workspace
                        ),
                        "decision": asdict(decision) if decision else None,
                        "snapshot": asdict(snapshot) if snapshot else None,
                        "approvals": approvals,
                        "fact_suggestions": fact_suggestions,
                    },
                )
            if method == "POST" and len(parts) == 5 and parts[4] == "pause-sla":
                self._require_role(user, "OWNER", "ADMIN")
                if case.sla_paused_at:
                    raise APIError(409, "STATE_CONFLICT", "SLA is already paused")
                body = self._body(environ)
                reason = str(body.get("reason", "")).strip()
                if not reason or len(reason) > 500:
                    raise APIError(422, "VALIDATION_ERROR", "reason is required and must be at most 500 characters")
                self.case_operations.pause_sla(case=case, user_id=user.user_id, reason=reason, paused_at=utc_now().isoformat())
                return self._json(200, {"case_id": cid, "sla_paused_at": case.sla_paused_at, "reason": reason})
            if method == "POST" and len(parts) == 5 and parts[4] == "resume-sla":
                self._require_role(user, "OWNER", "ADMIN")
                if not case.sla_paused_at:
                    raise APIError(409, "STATE_CONFLICT", "SLA is not paused")
                from datetime import datetime, timezone
                paused_seconds = self.case_operations.resume_sla(
                    case=case, user_id=user.user_id,
                    calendar=self._calendar(user.organization_id),
                    now=datetime.now(timezone.utc),
                )
                return self._json(200, {"case_id": cid, "sla_paused_seconds": round(case.sla_paused_seconds, 2)})
            if method == "GET" and len(parts) == 5 and parts[4] == "sla":
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review)
                signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get((user.organization_id, cid), [])
                suggestions = self.store.fact_suggestions.get((user.organization_id, cid), [])
                evidence_rows = [e for (eo, _), e in self.store.evidence.items() if eo == user.organization_id and e.get("case_id") == cid]
                                evidence = tuple(EvidenceView(e["evidence_id"],
                     e["filename"],
                     e.get("content_type") or "UNKNOWN",
                     e["sha256"],
                    "VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                                ws = CaseWorkspace(cid,
                     user.organization_id,
                     case.status,
                     "NORMAL",
                     ReviewSummary(review.review_id,
                     review.rating,
                     review.text,
                     review.published_at),
                     tuple(ClaimView(c.claim_id,
                    c.text,
                    c.claim_type,
                    "UNVERIFIED") for c in claims),
                     tuple(PolicySignalView(s.code,
                    s.status,
                    s.justification) for s in signals),
                     evidence,
                     (),
                     tuple(Contradiction(c["contradiction_id"],
                    c["description"],
                    c["claim_id"],
                    tuple(c["evidence_ids"]),
                    True) for c in contradictions))
                missing = missing_evidence_tasks(ws, {c.claim_id: [] for c in claims})
                                item = score_case(case_id=cid,
                     created_at=case.created_at,
                     policy_statuses=[s.status for s in signals],
                     contradiction_count=len(contradictions),
                     missing_evidence_count=len(missing),
                     unverified_suggestion_count=len([x for x in suggestions if not x.get("verified")]),
                    assigned_to=case.assigned_to)
                sla = self.case_sla.calculate(case, item.priority, self._calendar(user.organization_id))
                return self._json(200, {"case_id": cid, "sla": asdict(sla), "pause_reason": case.sla_pause_reason})
            if method == "POST" and len(parts) == 5 and parts[4] == "contradictions":
                self._require_role(user, "OWNER", "ADMIN")
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review)
                body = self._body(environ)
                requested_eids = body.get("evidence_ids")
                if requested_eids is not None and not isinstance(requested_eids, list):
                    raise APIError(422, "VALIDATION_ERROR", "evidence_ids must be a list")
                                selected = set(str(x) for x in requested_eids) if requested_eids is not None else {eid for (org,
                     eid),
                    e in self.store.evidence.items() if org == user.organization_id and e["case_id"] == cid}
                facts: list[EvidenceFact] = []
                for eid in sorted(selected):
                    e = self.store.evidence.get((user.organization_id, eid))
                    if not e or e["case_id"] != cid:
                        continue
                    for f in self.store.evidence_facts.get((user.organization_id, eid), []):
                        facts.append(EvidenceFact(eid, f["key"], f["kind"], f["value"], f.get("source_location", ""), bool(f.get("verified"))))
                rows = self.case_contradictions.analyze(
                    organization_id=user.organization_id,
                    case_id=cid,
                    user_id=user.user_id,
                    claims=claims,
                    evidence_facts=facts,
                    evidence_ids=sorted(selected),
                )
                self.store.contradictions[(user.organization_id, cid)] = rows
                return self._json(200, {"contradictions": rows, "count": len(rows), "requires_human_review": bool(rows)})
            if method == "POST" and len(parts) == 5 and parts[4] == "extract-facts":
                self._require_role(user, "OWNER", "ADMIN")
                body = self._body(environ)
                requested = body.get("evidence_ids")
                if requested is not None and not isinstance(requested, list):
                    raise APIError(422, "VALIDATION_ERROR", "evidence_ids must be a list")
                                selected = [str(x) for x in requested] if requested is not None else [eid for (org,
                     eid),
                    e in self.store.evidence.items() if org == user.organization_id and e["case_id"] == cid]
                all_suggestions = []
                for eid in selected:
                    e = self.store.evidence.get((user.organization_id, eid))
                    if not e or e["case_id"] != cid:
                        continue
                    try:
                        content = self.store.vault.get(organization_id=user.organization_id, object_key=e["object_key"])
                    except (KeyError, PermissionError):
                        continue
                    if not verify_integrity(content, e["sha256"]):
                        raise APIError(409, "INTEGRITY_ERROR", "evidence integrity check failed")
                    try:
                        extracted = extract_readable_text(content=content, content_type=e["content_type"], filename=e["filename"])
                    except (ExtractionError, UnicodeDecodeError, ValueError) as exc:
                        # Unsupported or unreadable evidence remains available
                        # for manual review; extraction failure is never a fact.
                        self.store.audit_event(
                            user.organization_id,
                            user.user_id,
                            "EVIDENCE_TEXT_EXTRACTION_FAILED",
                            f"evidence:{eid}",
                            case_id=cid,
                            reason=str(exc)[:240],
                        )
                        continue

                    suggestions = [
                        asdict(suggestion)
                        for suggestion in extract_text_fact_suggestions(
                            evidence_id=eid,
                            content=extracted.text.encode("utf-8"),
                            content_type="text/plain",
                        )
                    ]
                    for suggestion in suggestions:
                        suggestion["case_id"] = cid
                        suggestion["extraction_method"] = extracted.method
                        if self.repository is not None:
                            self.repository.put_fact_suggestion(
                                user.organization_id,
                                suggestion,
                            )
                    self.store.fact_suggestions[
                        (user.organization_id, eid)
                    ] = suggestions
                    all_suggestions.extend(suggestions)
                    self.store.audit_event(
                        user.organization_id,
                        user.user_id,
                        "EVIDENCE_TEXT_EXTRACTED",
                        f"evidence:{eid}",
                        case_id=cid,
                        method=extracted.method,
                        character_count=len(extracted.text),
                        suggestion_count=len(suggestions),
                    )

                self.store.audit_event(
                    user.organization_id,
                    user.user_id,
                    "EVIDENCE_FACTS_SUGGESTED",
                    f"case:{cid}",
                    suggestion_count=len(all_suggestions),
                    evidence_ids=selected,
                )
                return self._json(
                    200,
                    {
                        "suggestions": all_suggestions,
                        "count": len(all_suggestions),
                        "requires_human_review": bool(all_suggestions),
                        "verified": False,
                    },
                )
            if method == "GET" and len(parts) == 5 and parts[4] == "review-checklist":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER")
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review)
                signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get(
                    (user.organization_id, cid),
                    [],
                )
                suggestions = self.store.fact_suggestions.get(
                    (user.organization_id, cid),
                    [],
                )
                evidence_rows = [
                    evidence
                    for (organization_id, _), evidence in self.store.evidence.items()
                    if organization_id == user.organization_id
                    and evidence.get("case_id") == cid
                ]
                required = {}
                for signal in signals:
                    for claim_id in signal.claim_ids:
                        required.setdefault(claim_id, []).extend(
                            signal.evidence_required
                        )
                evidence = tuple(
                    EvidenceView(
                        item["evidence_id"],
                        item["filename"],
                        item.get("content_type") or "UNKNOWN",
                        item["sha256"],
                        "VERIFIED" if item.get("verified") else "UNVERIFIED",
                    )
                    for item in evidence_rows
                )
                workspace = CaseWorkspace(
                    cid,
                    user.organization_id,
                    case.status,
                    "NORMAL",
                    ReviewSummary(
                        review.review_id,
                        review.rating,
                        review.text,
                        review.published_at,
                    ),
                    tuple(
                        ClaimView(
                            claim.claim_id,
                            claim.text,
                            claim.claim_type,
                            "UNVERIFIED",
                        )
                        for claim in claims
                    ),
                    tuple(
                        PolicySignalView(
                            signal.code,
                            signal.status,
                            signal.justification,
                        )
                        for signal in signals
                    ),
                    evidence,
                    (),
                    tuple(
                        Contradiction(
                            item["contradiction_id"],
                            item["description"],
                            item["claim_id"],
                            tuple(item["evidence_ids"]),
                            True,
                        )
                        for item in contradictions
                    ),
                )
                missing = missing_evidence_tasks(workspace, required)
                checklist_items = self.case_review.ensure_checklist(
                    organization_id=user.organization_id,
                    case_id=cid,
                    has_policy_signals=bool(signals),
                    contradiction_count=len(contradictions),
                    unverified_fact_count=sum(
                        1 for item in suggestions if not item.get("verified")
                    ),
                    missing_evidence_count=len(missing),
                )
                readiness = self.case_review.readiness(
                    case_id=cid,
                    organization_id=user.organization_id,
                    items=checklist_items,
                    contradiction_count=len(contradictions),
                    unverified_fact_count=sum(
                        1 for item in suggestions if not item.get("verified")
                    ),
                    missing_evidence_count=len(missing),
                )
                return self._json(
                    200,
                    {
                        "items": checklist_items,
                        "readiness": asdict(readiness),
                    },
                )
            if method == "POST" and len(parts) == 5 and parts[4] == "review-checklist":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                body = self._body(environ)
                code = str(body.get("code", "")).strip()
                completed = body.get("completed")
                if not code or not isinstance(completed, bool):
                    raise APIError(
                        422,
                        "VALIDATION_ERROR",
                        "code and boolean completed are required",
                    )

                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review)
                signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get(
                    (user.organization_id, cid),
                    [],
                )
                suggestions = self.store.fact_suggestions.get(
                    (user.organization_id, cid),
                    [],
                )
                required = {}
                for signal in signals:
                    for claim_id in signal.claim_ids:
                        required.setdefault(claim_id, []).extend(
                            signal.evidence_required
                        )

                evidence_rows = [
                    evidence
                    for (organization_id, _), evidence in self.store.evidence.items()
                    if organization_id == user.organization_id
                    and evidence.get("case_id") == cid
                ]
                evidence = tuple(
                    EvidenceView(
                        item["evidence_id"],
                        item["filename"],
                        item.get("content_type") or "UNKNOWN",
                        item["sha256"],
                        "VERIFIED" if item.get("verified") else "UNVERIFIED",
                    )
                    for item in evidence_rows
                )
                workspace = CaseWorkspace(
                    cid,
                    user.organization_id,
                    case.status,
                    "NORMAL",
                    ReviewSummary(
                        review.review_id,
                        review.rating,
                        review.text,
                        review.published_at,
                    ),
                    tuple(
                        ClaimView(
                            claim.claim_id,
                            claim.text,
                            claim.claim_type,
                            "UNVERIFIED",
                        )
                        for claim in claims
                    ),
                    tuple(
                        PolicySignalView(
                            signal.code,
                            signal.status,
                            signal.justification,
                        )
                        for signal in signals
                    ),
                    evidence,
                    (),
                    tuple(
                        Contradiction(
                            item["contradiction_id"],
                            item["description"],
                            item["claim_id"],
                            tuple(item["evidence_ids"]),
                            True,
                        )
                        for item in contradictions
                    ),
                )
                missing = missing_evidence_tasks(workspace, required)
                self.case_review.ensure_checklist(
                    organization_id=user.organization_id,
                    case_id=cid,
                    has_policy_signals=bool(signals),
                    contradiction_count=len(contradictions),
                    unverified_fact_count=sum(
                        1 for item in suggestions if not item.get("verified")
                    ),
                    missing_evidence_count=len(missing),
                )
                try:
                    row = self.case_review.update_item(
                        organization_id=user.organization_id,
                        case_id=cid,
                        code=code,
                        completed=completed,
                        user_id=user.user_id,
                        note=body.get("note"),
                    )
                except KeyError as exc:
                    raise APIError(
                        404,
                        "NOT_FOUND",
                        "checklist item not found",
                    ) from exc
                return self._json(200, {"item": row})

            if method == "GET" and len(parts) == 5 and parts[4] == "review-readiness":
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review)
                signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get(
                    (user.organization_id, cid),
                    [],
                )
                suggestions = self.store.fact_suggestions.get(
                    (user.organization_id, cid),
                    [],
                )
                evidence_rows = [
                    evidence
                    for (organization_id, _), evidence in self.store.evidence.items()
                    if organization_id == user.organization_id
                    and evidence.get("case_id") == cid
                ]
                evidence = tuple(
                    EvidenceView(
                        item["evidence_id"],
                        item["filename"],
                        item.get("content_type") or "UNKNOWN",
                        item["sha256"],
                        "VERIFIED" if item.get("verified") else "UNVERIFIED",
                    )
                    for item in evidence_rows
                )
                workspace = CaseWorkspace(
                    cid,
                    user.organization_id,
                    case.status,
                    "NORMAL",
                    ReviewSummary(
                        review.review_id,
                        review.rating,
                        review.text,
                        review.published_at,
                    ),
                    tuple(
                        ClaimView(
                            claim.claim_id,
                            claim.text,
                            claim.claim_type,
                            "UNVERIFIED",
                        )
                        for claim in claims
                    ),
                    tuple(
                        PolicySignalView(
                            signal.code,
                            signal.status,
                            signal.justification,
                        )
                        for signal in signals
                    ),
                    evidence,
                    (),
                    tuple(
                        Contradiction(
                            item["contradiction_id"],
                            item["description"],
                            item["claim_id"],
                            tuple(item["evidence_ids"]),
                            True,
                        )
                        for item in contradictions
                    ),
                )
                missing = missing_evidence_tasks(
                    workspace,
                    {claim.claim_id: [] for claim in claims},
                )
                items = self.case_review.ensure_checklist(
                    organization_id=user.organization_id,
                    case_id=cid,
                    has_policy_signals=bool(signals),
                    contradiction_count=len(contradictions),
                    unverified_fact_count=sum(
                        1 for item in suggestions if not item.get("verified")
                    ),
                    missing_evidence_count=len(missing),
                )
                readiness = self.case_review.readiness(
                    case_id=cid,
                    organization_id=user.organization_id,
                    items=items,
                    contradiction_count=len(contradictions),
                    unverified_fact_count=sum(
                        1 for item in suggestions if not item.get("verified")
                    ),
                    missing_evidence_count=len(missing),
                )
                return self._json(
                    200,
                    {
                        "readiness": asdict(readiness),
                        "human_review_required": True,
                    },
                )
            if method == "GET" and len(parts) == 5 and parts[4] == "contradictions":
                rows = self.store.contradictions.get((user.organization_id, cid), [])
                out=[]
                for row in rows:
                    item=dict(row)
                    item["disposition"]=self.store.contradiction_dispositions.get((user.organization_id,row["contradiction_id"]))
                    out.append(item)
                return self._json(200, {"contradictions": out, "count": len(out), "requires_human_review": bool(out)})
            if method == "GET" and len(parts) == 7 and parts[4] == "contradictions" and parts[6] == "history":
                contradiction_id=parts[5]
                rows=self.store.contradictions.get((user.organization_id,cid),[])
                if not any(x.get("contradiction_id")==contradiction_id for x in rows):
                    raise APIError(404,"NOT_FOUND","contradiction not found")
                history=list(self.store.contradiction_disposition_history.get((user.organization_id,contradiction_id),[]))
                if self.repository is not None and hasattr(self.repository,"list_contradiction_disposition_history"):
                    try:
                        history=self.repository.list_contradiction_disposition_history(user.organization_id,contradiction_id) or history
                    except Exception:
                        pass
                return self._json(
                    200,
                    {
                        "history": history,
                        "count": len(history),
                        "requires_human_review": True,
                    },
                )
            if method == "GET" and len(parts) == 5 and parts[4] == "evidence-matrix":
                case=self.store.cases.get((user.organization_id,cid))
                if case is None:
                    raise APIError(404,"NOT_FOUND","case not found")
                try:
                    matrix=self.case_evidence_matrix.build(
                        organization_id=user.organization_id,
                        case=case,
                    )
                except KeyError as exc:
                    raise APIError(404,"NOT_FOUND",str(exc)) from exc
                return self._json(
                    200,
                    {
                        "case_id": cid,
                        "matrix": matrix,
                        "count": len(matrix),
                        "requires_human_review": True,
                    },
                )
            if (
                method == "GET"
                and len(parts) == 6
                and parts[4] == "contradictions"
                and parts[5]
                in {
                    item["contradiction_id"]
                    for item in self.store.contradictions.get(
                        (user.organization_id, cid),
                        [],
                    )
                }
            ):
                contradiction_id = parts[5]
                row = next(
                    item
                    for item in self.store.contradictions[
                        (user.organization_id, cid)
                    ]
                    if item["contradiction_id"] == contradiction_id
                )
                return self._json(
                    200,
                    {
                        "contradiction": row,
                        "disposition": self.store.contradiction_dispositions.get(
                            (user.organization_id, contradiction_id)
                        ),
                    },
                )
            if method == "POST" and len(parts) == 7 and parts[4] == "contradictions" and parts[6] == "disposition":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                contradiction_id=parts[5]
                rows=self.store.contradictions.get((user.organization_id,cid),[])
                if not any(x.get("contradiction_id")==contradiction_id for x in rows):
                    raise APIError(404,"NOT_FOUND","contradiction not found")
                body=self._body(environ)
                try:
                    d = self.case_contradictions.disposition(
                        organization_id=user.organization_id,
                        case_id=cid,
                        contradiction_id=contradiction_id,
                        status=body.get("status"),
                        rationale=body.get("rationale"),
                        actor_id=user.user_id,
                    )
                except ValueError as exc:
                    raise APIError(422,"VALIDATION_ERROR",str(exc))
                return self._json(200,{"disposition":d,"requires_human_review":True})
            if method == "POST" and len(parts) == 5 and parts[4] == "decision":
                self._require_role(user, "OWNER", "ADMIN")
                body = self._body(environ)
                kind = body.get("kind", "HUMAN_REVIEW")
                rationale = str(body.get("rationale", ""))
                if not rationale.strip():
                    raise APIError(422, "VALIDATION_ERROR", "rationale is required")
                decision = self.case_decisions.create(
                    case=case,
                    user_id=user.user_id,
                    kind=kind,
                    rationale=rationale,
                )
                return self._json(201, {"decision": asdict(decision)})
            if method == "POST" and len(parts) == 5 and parts[4] == "freeze":
                self._require_role(user, "OWNER", "ADMIN")
                if not case.decision_id:
                    raise APIError(409, "STATE_CONFLICT", "decision required before freeze")
                decision, snap = self.case_decisions.freeze(
                    case=case,
                    user_id=user.user_id,
                )
                return self._json(200, {"decision": asdict(decision), "snapshot_sha256": snap.sha256})
            if method == "POST" and len(parts) == 5 and parts[4] == "approve":
                self._require_role(user, "OWNER", "ADMIN")
                if (
                    not case.decision_id
                    or (user.organization_id, cid) not in self.store.snapshots
                ):
                    raise APIError(
                        409,
                        "STATE_CONFLICT",
                        "frozen decision required",
                    )
                try:
                    approved, event = self.case_decisions.approve(
                        case=case,
                        user_id=user.user_id,
                        user_role=user.role,
                    )
                except (ValueError, PermissionError) as exc:
                    raise APIError(409, "APPROVAL_REJECTED", str(exc)) from exc
                return self._json(200, {"decision": asdict(approved), "approval": asdict(event)})
            if method == "POST" and len(parts) == 5 and parts[4] == "submit":
                self._require_role(user, "OWNER", "ADMIN")
                if not case.decision_id:
                    raise APIError(409, "STATE_CONFLICT", "decision required")
                body = self._body(environ)
                def submit():
                    try:
                        row = self.case_submissions.prepare(case=case, user_id=user.user_id)
                    except ValueError as exc:
                        raise APIError(409, "APPROVAL_REQUIRED", str(exc)) from exc
                    return {"submission": row}
                return self._json(201, self._idem(user, environ, body, submit))
            raise APIError(404, "NOT_FOUND", "case operation not found")
        if method == "POST" and path == "/v1/logout":
            header = environ.get("HTTP_AUTHORIZATION", "")
            raw = header[7:].strip() if header.startswith("Bearer ") else ""
            th = __import__("hashlib").sha256(raw.encode()).hexdigest()
            old = self.store.sessions.get(th)
            if old:
                self.store.sessions[th] = Session(old.user_id, old.organization_id, old.role, old.token_hash, old.expires_at, utc_now())
                if self.repository is not None:
                    self.repository.revoke_session(user.organization_id, th)
                if hasattr(self.repository, "security_event"):
                    self.repository.security_event(
                        user.organization_id,
                        user.user_id,
                        "LOGOUT",
                        user.user_id,
                        {"ip_hash": self._client_ip_hash(environ)},
                    )
                self.store.audit_event(user.organization_id, user.user_id, "LOGOUT", "session")
            clear_cookie = (
                f"{self._session_cookie_name()}=; Path=/; Max-Age=0; "
                f"HttpOnly; SameSite=Lax"
                + ("; Secure" if self.config.production else "")
            )
            return self._json(
                200,
                {"status": "logged_out"},
                headers={"Set-Cookie": clear_cookie},
            )
        raise APIError(404, "NOT_FOUND", "route not found")

    def __call__(self, environ, start_response):
        """Adaptateur WSGI : trace, exceptions, métriques et en-têtes HTTP.

        Les APIError conservent leur statut et leur code ; les exceptions
        inattendues sont masquées derrière INTERNAL_ERROR côté client.
        """
        # V6.29: every request receives a correlation ID and bounded telemetry.
        import time as _time
        started = _time.perf_counter()
        trace_id = environ.get("HTTP_X_REQUEST_ID") or __import__("secrets").token_hex(16)
        environ["review_defense.trace_id"] = trace_id
        # V6.3 operations console: serve the static frontend from the same
        # origin as the API, avoiding a separate trust boundary in the reference
        # deployment. The frontend never embeds secrets and only talks to /v1.
        path = urlsplit(environ.get("PATH_INFO", "/")).path
        # V6.39: crawlable public SEO pages and technical SEO endpoints.
        if environ.get("REQUEST_METHOD") == "GET" and is_seo_path(path):
            body = render_page(path)
            self.telemetry.increment("http_requests_total", labels={"method":"GET","path":path,"status":"200"})
            self.telemetry.observe_ms("http_request_duration_ms", (_time.perf_counter()-started)*1000, labels={"method":"GET","path":path})
            headers = [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("X-Request-ID", trace_id),
            ]
            if self.config.secure_headers:
                headers.extend(list(security_headers(production=self.config.production).items()))
            start_response("200 OK", headers)
            return [body]
        if path == "/robots.txt" and environ.get("REQUEST_METHOD") == "GET":
            body = robots()
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/plain; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("X-Request-ID", trace_id),
                    *(
                        list(security_headers(production=self.config.production).items())
                        if self.config.secure_headers
                        else []
                    ),
                ],
            )
            return [body]
        if path == "/sitemap.xml" and environ.get("REQUEST_METHOD") == "GET":
            body = sitemap()
            start_response(
                "200 OK",
                [
                    ("Content-Type", "application/xml; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("X-Request-ID", trace_id),
                    *(
                        list(security_headers(production=self.config.production).items())
                        if self.config.secure_headers
                        else []
                    ),
                ],
            )
            return [body]
        if path == "/":
            path = "/index.html"
        elif (
            path == "/app"
            or path.startswith("/app/")
            or path in {"/login", "/register"}
        ):
            path = "/dist/react.html"
        elif path.startswith("/react/"):
            path = "/dist/" + path[len("/react/"):]
        elif path in {
            "/client",
            "/client/",
            "/admin",
            "/admin/",
            "/connexion",
            "/inscription",
            "/verify-email",
        }:
            path = "/workspace.html"        elif path in {"/client", "/client/", "/admin", "/admin/", "/connexion", "/inscription", "/verify-email"}:
            path = "/workspace.html"
        elif path in {
            "/conformite/","/produit/","/comment-ca-marche/","/services/","/tarifs/","/ressources/",
            "/contact/","/mentions-legales/","/confidentialite/","/cgv/","/cgu/","/cookies/",
            "/securite/","/conservation-donnees/","/droits-rgpd/","/violation-donnees/",
            "/sous-traitants/","/ia-et-controle-humain/",
            "/accept-invitation","/reset-password",
        }:
            # Public marketing and authentication deep links use the same stable frontend shell.
            # Serving index.html here keeps direct navigation and refreshes working.
            path = "/index.html"
        if path in {
            "/index.html",
            "/landing.html",
            "/workspace.html",
            "/workspace.js",
            "/workspace.css",
            "/styles.css",
            "/script.js",
        } or path.startswith("/assets/") or path.startswith("/dist/"):
            from pathlib import Path
            import mimetypes
            root = Path(__file__).resolve().parents[1] / "frontend"
            rel = path.lstrip("/")
            target = (root / rel).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                target = None
            if target and target.is_file():
                body = target.read_bytes()
                ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                if target.suffix.lower() in {".js", ".css", ".html"}:
                    ctype = ctype + "; charset=utf-8"
                elapsed = (_time.perf_counter() - started) * 1000
                self.telemetry.increment("http_requests_total", labels={"method": environ.get("REQUEST_METHOD", "GET"), "path": path, "status": "200"})
                self.telemetry.observe_ms("http_request_duration_ms", elapsed, labels={"method": environ.get("REQUEST_METHOD", "GET"), "path": path})
                response_headers = [
                    ("Content-Type", ctype),
                    ("Content-Length", str(len(body))),
                    ("X-Request-ID", trace_id),
                    ("Cache-Control", "no-cache"),
                ]
                if self.config.secure_headers:
                    response_headers.extend(
                        security_headers(production=self.config.production).items()
                    )
                start_response("200 OK", response_headers)
                return [body]
        try:
            status, headers, body = self.handle(environ)
        except APIError as exc:
            status, headers, body = self._json(exc.status, {"error": {"code": exc.code, "message": exc.message, "details": exc.details}})
        except Exception:
            status, headers, body = self._json(500, {"error": {"code": "INTERNAL_ERROR", "message": "internal server error"}})
        phrase = {
            200: "OK",
            201: "Created",
            302: "Found",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            409: "Conflict",
            413: "Payload Too Large",
            415: "Unsupported Media Type",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
        }.get(status, "Error")
        elapsed = (_time.perf_counter() - started) * 1000
        self.telemetry.increment("http_requests_total", labels={"method": environ.get("REQUEST_METHOD", "GET"), "path": path, "status": str(status)})
        self.telemetry.observe_ms("http_request_duration_ms", elapsed, labels={"method": environ.get("REQUEST_METHOD", "GET"), "path": path})
        if status >= 500:
            self.telemetry.increment("http_errors_total", labels={"path": path, "status": str(status)})
        response_headers = [(k,v) for k,v in headers.items()] + [("Content-Length", str(len(body))), ("X-Request-ID", trace_id)]
        if self.config.secure_headers:
            response_headers.extend(list(security_headers(production=self.config.production).items()))
            response_headers.append(("Cache-Control", "no-store"))
        start_response(f"{status} {phrase}", response_headers)
        return [body]


def create_app(*, store: MemoryStore | None = None, repository=None, config: ProductionConfig | None = None) -> ReviewDefenseAPI:
    """Construit l'API et crée le repository PostgreSQL si DATABASE_URL existe.

    wsgi.py appelle cette factory pour fournir l'objet chargé par Gunicorn.
    """
    config = config or ProductionConfig.from_env()
    if repository is None and config.database_dsn:
        from .postgres_api_repository import PostgresAPIRepository
        repository = PostgresAPIRepository(config.database_dsn)
    return ReviewDefenseAPI(store=store, repository=repository, config=config)


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    from wsgiref.simple_server import make_server
    app = create_app()
    with make_server(host, port, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    serve()
