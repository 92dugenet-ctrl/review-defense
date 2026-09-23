"""V6.0 production HTTP/API boundary for Review Defense.

Framework-neutral WSGI application. The reference implementation deliberately
uses in-memory stores so the HTTP contract can be exercised without a running
PostgreSQL/Google service. Production adapters can replace the stores while
keeping the route/auth/error/idempotency contracts.
"""
from __future__ import annotations

import base64
import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs, urlsplit

from .evidence_vault import InMemoryObjectStore, sign_download_url, verify_integrity
from .security_hardening import RateLimiter, Session, generate_session_token, hash_password, verify_password, utc_now, hash_token
from .app_shell import SessionContext, can_access
from .decision_workspace import (
    attach_snapshot, approve_decision, create_decision, freeze_dossier,
    request_approval, can_approve_decision, can_create_decision,
)
from .review_workspace import ReviewContext, extract_claims, classify_policy_signals
from .contradiction_engine import EvidenceFact, detect_contradictions
from .evidence_extraction import extract_text_fact_suggestions
from .evidence_ocr import extract_readable_text, ExtractionError
from .review_queue import score_case, sort_queue
from .review_sla import calculate_sla
from .business_calendar import calendar_from_dict, default_calendar
from .escalation_workflow import Escalation, signal_from_sla
from .notification_outbox import Notification, create_notification
from .notification_delivery import deliver, DeliveryError
from .notification_worker import NotificationWorker
from .notification_policy import NotificationPolicy, validate_policy, evaluate
from .notification_observability import build_notification_metrics
from .case_review import ReviewChecklistItem, build_checklist, assess_readiness
from .contradiction_disposition import make_disposition, validate_disposition
from .case_review_matrix import build_evidence_matrix
from .operations_ui import (
    ReviewSummary, ClaimView, PolicySignalView, EvidenceView, TimelineEvent,
    Contradiction, CaseWorkspace, missing_evidence_tasks, case_requires_human_review,
)
from .identity import normalize_email, validate_role, issue_session, can_manage_org
from .production_config import ProductionConfig
from .mfa import generate_secret, verify_totp, otpauth_uri, encrypt_secret, decrypt_secret, recovery_token
from .recovery_email import SMTPConfig, send_recovery_email, send_verification_email, RecoveryEmailError
from .deployment import DeploymentConfig, security_headers
from .observability import InMemoryTelemetry, TraceContext, health_check
from .seo_renderer import is_seo_path, render_page, sitemap, robots


class APIError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


@dataclass(frozen=True)
class User:
    user_id: str
    organization_id: str
    email: str
    password_hash: str
    role: str


@dataclass
class Case:
    case_id: str
    organization_id: str
    review_id: str
    status: str = "NEW"
    decision_id: str | None = None
    snapshot_sha256: str | None = None
    assigned_to: str | None = None
    created_at: str | None = None
    sla_paused_at: str | None = None
    sla_paused_seconds: float = 0.0
    sla_pause_reason: str | None = None


class MemoryStore:
    def __init__(self) -> None:
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
        self.email_verified: dict[str, bool] = {}

    def audit_event(self, org: str, actor: str | None, action: str, resource: str, **meta: Any) -> None:
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
    """Small WSGI API with explicit human-gated state transitions."""
    def __init__(self, store: MemoryStore | None = None, *, session_ttl: int = 3600,
                 limiter: RateLimiter | None = None, repository=None, delivery_email_config: dict[str, Any] | None = None, delivery_func=deliver, config: ProductionConfig | None = None):
        self.store = store or MemoryStore()
        self.config = config or ProductionConfig.from_env()
        self.config.validate_startup(require_database=(repository is not None or self.config.production))
        self.repository = repository
        self.delivery_email_config = delivery_email_config or {}
        if not self.delivery_email_config and self.config.smtp_host and self.config.smtp_sender:
            self.delivery_email_config = {
                "host": self.config.smtp_host, "port": self.config.smtp_port,
                "username": self.config.smtp_username, "password": self.config.smtp_password,
                "sender": self.config.smtp_sender, "starttls": self.config.smtp_starttls,
            }
        self.delivery_func = delivery_func
        self.notification_worker = NotificationWorker(delivery_func=delivery_func, email_config=self.delivery_email_config)
        self.session_ttl = session_ttl
        self.limiter = limiter or RateLimiter(limit=120, window_seconds=60)
        self.auth_limiter = RateLimiter(limit=8, window_seconds=300)
        self.recovery_limiter = RateLimiter(limit=5, window_seconds=3600)
        self._idem_lock = __import__("threading").RLock()
        self.telemetry = InMemoryTelemetry()
        DeploymentConfig(public_base_url=self.config.public_base_url, environment=self.config.environment, trust_proxy=self.config.trust_proxy).validate() if self.config.production else None
        self.store.sla_calendars = self.store.sla_calendars
        self.store.escalations = self.store.escalations
        self.store.notifications = self.store.notifications

    def _client_ip_hash(self, environ) -> str:
        import hashlib
        ip = environ.get("REMOTE_ADDR", "unknown") or "unknown"
        return hashlib.sha256(ip.encode()).hexdigest()

    def _user_agent(self, environ) -> str | None:
        value = environ.get("HTTP_USER_AGENT")
        return value[:512] if isinstance(value, str) else None

    def _auth_key(self, environ, email: str) -> str:
        return f"{environ.get('REMOTE_ADDR', 'unknown')}:{email}"

    def _calendar(self, organization_id: str):
        if organization_id not in self.store.sla_calendars and self.repository is not None and hasattr(self.repository, "get_sla_calendar"):
            row = self.repository.get_sla_calendar(organization_id)
            if row: self.store.sla_calendars[organization_id] = row
        return calendar_from_dict(self.store.sla_calendars.get(organization_id)) if organization_id in self.store.sla_calendars else default_calendar()

    def _notification_policy(self, organization_id: str):
        if organization_id not in self.store.notification_policies and self.repository is not None and hasattr(self.repository, "get_notification_policy"):
            row = self.repository.get_notification_policy(organization_id)
            if row:
                self.store.notification_policies[organization_id] = validate_policy(organization_id, row)
        return self.store.notification_policies.get(organization_id) or validate_policy(organization_id, {})

    def _escalation_for(self, organization_id: str, case_id: str, sla):
        signal = signal_from_sla(case_id, sla)
        if signal is None:
            return self.store.escalations.get((organization_id, case_id, "DUE")) or self.store.escalations.get((organization_id, case_id, "CRITICAL"))
        key = (organization_id, case_id, signal.level)
        existing = self.store.escalations.get(key)
        if existing:
            return existing
        if self.repository is not None and hasattr(self.repository, "get_escalation"):
            row = self.repository.get_escalation(organization_id, case_id, signal.level)
            if row:
                signal = Escalation(**row)
        self.store.escalations[key] = signal
        return signal

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

    def _json(self, status: int, payload: Mapping[str, Any], headers: Mapping[str, str] | None = None):
        return status, {"Content-Type": "application/json; charset=utf-8", **(headers or {})}, json.dumps(payload, ensure_ascii=False).encode()

    def _auth(self, environ) -> User:
        header = environ.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Bearer "):
            raise APIError(401, "AUTH_REQUIRED", "authentication required")
        raw = header[7:].strip()
        token_hash = hash_token(raw)
        session = self.store.sessions.get(token_hash)
        if session is None and self.repository is not None:
            # Production adapters may expose a persistent session row. The repository
            # contract is deliberately tenant-bound, so the token is first matched
            # against the in-memory user index when available.
            for candidate in self.store.users.values():
                row = self.repository.get_session(candidate.organization_id, token_hash)
                if row:
                    _, uid, org, role, expires_at, revoked_at = row
                    from datetime import datetime
                    def parse(v):
                        if isinstance(v, datetime): return v
                        return datetime.fromisoformat(str(v).replace('Z','+00:00'))
                    session = Session(str(uid), str(org), str(role), token_hash, parse(expires_at), parse(revoked_at) if revoked_at else None)
                    self.store.sessions[token_hash] = session
                    break
        if session is None or not session.active():
            raise APIError(401, "AUTH_INVALID", "invalid or expired session")
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
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
            limit = 35_000_000 if environ.get("PATH_INFO", "").startswith("/v1/evidence") else 1_000_000
            if length > limit:
                raise APIError(413, "PAYLOAD_TOO_LARGE", "request body too large")
            raw = environ["wsgi.input"].read(length) if length else b"{}"
            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict):
                raise ValueError
            return obj
        except APIError:
            raise
        except Exception as exc:
            raise APIError(400, "INVALID_JSON", "request body must be a JSON object") from exc

    def _idem(self, user: User, environ, body: Mapping[str, Any], producer: Callable[[], Any]):
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
        if user.role not in roles:
            raise APIError(403, "FORBIDDEN", "role is not permitted for this operation")

    def _mfa_key(self) -> str:
        import os
        key = os.getenv("REVIEW_DEFENSE_MFA_ENCRYPTION_KEY", "")
        if not key:
            if self.config.environment == "production":
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
                state = {"enabled": bool(row[0]), "secret_enc": row[1]}
                self.store.mfa[user.user_id] = state
                return state
        return {"enabled": False, "secret_enc": None}

    def _mfa_secret(self, user: User) -> str | None:
        state = self._mfa_state(user)
        if not state.get("enabled") or not state.get("secret_enc"):
            return None
        return decrypt_secret(state["secret_enc"], self._mfa_key())

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
        body = ("\n".join(lines) + "\n").encode()
        return 200, {"Content-Type": "text/plain; version=0.0.4; charset=utf-8"}, body

    def handle(self, environ):
        path = urlsplit(environ.get("PATH_INFO", "/")).path.rstrip("/") or "/"
        method = environ.get("REQUEST_METHOD", "GET").upper()
        if not self.limiter.allow(environ.get("REMOTE_ADDR", "unknown")):
            raise APIError(429, "RATE_LIMITED", "rate limit exceeded")
        if method == "GET" and path == "/health":
            result = health_check(checks={"store": lambda: self.store is not None})
            return self._json(200 if result.status == "ok" else 503, {"status": result.status, "service": "review-defense", "version": "6.40", "checks": result.checks, "checked_at": result.checked_at})
        if method == "GET" and path == "/metrics":
            # Prometheus-compatible metrics contain only aggregate operational data.
            import os
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
        if method == "POST" and path == "/v1/auth/recovery/request":
            body = self._body(environ)
            try:
                email = normalize_email(str(body.get("email", "")))
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            organization_id = str(body.get("organization_id", "")).strip()
            if not organization_id:
                raise APIError(422, "VALIDATION_ERROR", "organization_id is required")
            if not self.recovery_limiter.allow(self._auth_key(environ, email)):
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
                self.store.recovery_tokens[token_hash] = {"organization_id":organization_id,"user_id":user.user_id,"expires_at":expires.isoformat(),"used_at":None}
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
                import os
                if os.getenv("REVIEW_DEFENSE_EXPOSE_RECOVERY_TOKEN", "false").lower() == "true" and self.config.environment != "production":
                    return self._json(200, {"status":"requested", "recovery_token":raw, "expires_at":expires.isoformat()})
            return self._json(200, {"status":"requested"})

        if method == "POST" and path == "/v1/auth/recovery/reset":
            body = self._body(environ)
            organization_id = str(body.get("organization_id", "")).strip()
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
                if urow: user = User(str(urow[0]), organization_id, str(urow[1]), str(urow[2]), str(urow[3]))
            if user is None: raise APIError(400, "RECOVERY_INVALID", "recovery token is invalid")
            updated = User(user.user_id,user.organization_id,user.email,new_hash,user.role); self.store.users[user.user_id]=updated
            for th, sess in list(self.store.sessions.items()):
                if sess.user_id == user.user_id and sess.organization_id == organization_id:
                    self.store.sessions[th] = Session(sess.user_id,sess.organization_id,sess.role,sess.token_hash,sess.expires_at,utc_now())
            if self.repository is not None:
                if hasattr(self.repository,"update_password"): self.repository.update_password(organization_id,user.user_id,new_hash)
                if hasattr(self.repository,"consume_recovery_token"): self.repository.consume_recovery_token(organization_id,token_hash)
                if hasattr(self.repository,"security_event"): self.repository.security_event(organization_id,user.user_id,"PASSWORD_RECOVERED",user.user_id)
            row["used_at"] = utc_now().isoformat()
            self.store.audit_event(organization_id,user.user_id,"PASSWORD_RECOVERED",f"user:{user.user_id}")
            return self._json(200,{"status":"password_reset"})

        if method == "POST" and path == "/v1/auth/email-verification/verify":
            body = self._body(environ)
            organization_id = str(body.get("organization_id", "")).strip()
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
                if hasattr(self.repository, "mark_email_verified"): self.repository.mark_email_verified(organization_id, user_id)
                if hasattr(self.repository, "consume_email_verification_token"): self.repository.consume_email_verification_token(organization_id, token_hash)
                if hasattr(self.repository, "security_event"): self.repository.security_event(organization_id, user_id, "EMAIL_VERIFIED", user_id)
            self.store.audit_event(organization_id, user_id, "EMAIL_VERIFIED", f"user:{user_id}")
            return self._json(200, {"status": "email_verified"})

        if method == "POST" and path == "/v1/auth/login":
            body = self._body(environ)
            try:
                email = normalize_email(str(body.get("email", "")))
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            if not self.auth_limiter.allow(self._auth_key(environ, email)):
                raise APIError(429, "AUTH_RATE_LIMITED", "too many authentication attempts")
            password = body.get("password", "")
            user = None
            organization_id = str(body.get("organization_id", "")).strip()
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
            mfa_secret = self._mfa_secret(user)
            if mfa_secret is not None:
                if not verify_totp(mfa_secret, str(body.get("mfa_code", ""))):
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
            token = str(body.get("invitation_token", "")); email = normalize_email(str(body.get("email", "")))
            password = body.get("password", "")
            token_hash = hash_token(token)
            invitation = next((i for i in self.store.invitations.values() if i.get("token_hash") == token_hash), None)
            if invitation is None or invitation.get("email") != email or invitation.get("accepted_at") or invitation.get("revoked_at"):
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
                    if hasattr(self.repository,"update_password"): self.repository.update_password(invitation["organization_id"],uid,ph)
                    if hasattr(self.repository,"update_role"): self.repository.update_role(invitation["organization_id"],uid,invitation["role"])
            else:
                uid=str(uuid.uuid4()); new_user=User(uid,invitation["organization_id"],email,ph,invitation["role"]); self.store.users[uid]=new_user
                if self.repository is not None and hasattr(self.repository,"create_user"):
                    rid,*_=self.repository.create_user(invitation["organization_id"],email,ph,invitation["role"]); uid=str(rid); self.store.users.pop(uid,None); self.store.users[rid]=User(rid,invitation["organization_id"],email,ph,invitation["role"])
            invitation["accepted_at"]=utc_now().isoformat()
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
            return self._json(200,{"status":"accepted","access_token":raw,"token_type":"Bearer","expires_at":session.expires_at.isoformat(),"role":invitation["role"]})
        user = self._auth(environ)
        # All v1 routes are tenant-bound to the authenticated user. There is no organization_id override.
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
            if self._mfa_state(user).get("enabled"):
                raise APIError(409, "MFA_ALREADY_ENABLED", "MFA is already enabled")
            secret = generate_secret(); encrypted = encrypt_secret(secret, self._mfa_key())
            self.store.mfa[user.user_id] = {"enabled":False,"secret_enc":encrypted,"pending":True}
            if self.repository is not None and hasattr(self.repository,"set_mfa_secret"):
                self.repository.set_mfa_secret(user.organization_id,user.user_id,encrypted,False)
            self.store.audit_event(user.organization_id,user.user_id,"MFA_ENROLLMENT_STARTED",f"user:{user.user_id}")
            return self._json(200,{"status":"pending","secret":secret,"otpauth_uri":otpauth_uri(secret,user.email)})

        if method == "POST" and path == "/v1/auth/mfa/confirm":
            state=self._mfa_state(user)
            if not state.get("secret_enc"): raise APIError(400,"MFA_NOT_ENROLLED","MFA enrollment has not been started")
            secret=decrypt_secret(state["secret_enc"],self._mfa_key())
            if not verify_totp(secret,str(self._body(environ).get("code",""))): raise APIError(401,"MFA_INVALID","invalid MFA code")
            state={"enabled":True,"secret_enc":state["secret_enc"]}; self.store.mfa[user.user_id]=state
            if self.repository is not None and hasattr(self.repository,"set_mfa_secret"): self.repository.set_mfa_secret(user.organization_id,user.user_id,state["secret_enc"],True)
            self.store.audit_event(user.organization_id,user.user_id,"MFA_ENABLED",f"user:{user.user_id}")
            return self._json(200,{"status":"enabled"})

        if method == "POST" and path == "/v1/auth/mfa/disable":
            self._require_role(user,"OWNER","ADMIN")
            body=self._body(environ); current=str(body.get("password","")); code=str(body.get("mfa_code",""))
            if not verify_password(current,user.password_hash): raise APIError(401,"AUTH_INVALID","password is invalid")
            secret=self._mfa_secret(user)
            if secret is not None and not verify_totp(secret,code): raise APIError(401,"MFA_INVALID","valid MFA code is required")
            self.store.mfa[user.user_id]={"enabled":False,"secret_enc":None}
            if self.repository is not None and hasattr(self.repository,"disable_mfa"): self.repository.disable_mfa(user.organization_id,user.user_id)
            self.store.audit_event(user.organization_id,user.user_id,"MFA_DISABLED",f"user:{user.user_id}")
            return self._json(200,{"status":"disabled"})

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
                if sess.user_id == user.user_id:
                    self.store.sessions[th] = Session(sess.user_id, sess.organization_id, sess.role, sess.token_hash, sess.expires_at, utc_now())
            # Issue a fresh session after revoking all previous sessions.
            raw, fresh = issue_session(user_id=user.user_id, organization_id=user.organization_id, role=user.role, ttl_seconds=self.session_ttl)
            self.store.sessions[fresh.token_hash] = fresh
            if self.repository is not None:
                if hasattr(self.repository, "update_password"): self.repository.update_password(user.organization_id, user.user_id, new_hash)
                if hasattr(self.repository, "put_session"): self.repository.put_session(user.organization_id, fresh.token_hash, user.user_id, user.role, fresh.expires_at.isoformat())
                if hasattr(self.repository, "security_event"): self.repository.security_event(user.organization_id, user.user_id, "PASSWORD_CHANGED", user.user_id)
            self.store.audit_event(user.organization_id, user.user_id, "PASSWORD_CHANGED", f"user:{user.user_id}")
            return self._json(200, {"status":"password_changed", "access_token":raw, "token_type":"Bearer", "expires_at":fresh.expires_at.isoformat()})
        if method == "POST" and path == "/v1/auth/rotate":
            old_raw = environ.get("HTTP_AUTHORIZATION", "")[7:].strip()
            old_hash = hash_token(old_raw)
            old = self.store.sessions.get(old_hash)
            if old is None: raise APIError(401, "AUTH_INVALID", "invalid session")
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
            target = str(self._body(environ).get("user_id", user.user_id))
            target_user = self.store.users.get(target)
            if target_user is None or target_user.organization_id != user.organization_id:
                raise APIError(404, "NOT_FOUND", "user not found")
            for th, sess in list(self.store.sessions.items()):
                if sess.user_id == target:
                    self.store.sessions[th] = Session(sess.user_id, sess.organization_id, sess.role, sess.token_hash, sess.expires_at, utc_now())
            if self.repository is not None and hasattr(self.repository, "revoke_all_sessions"):
                self.repository.revoke_all_sessions(user.organization_id, target)
                if hasattr(self.repository, "security_event"):
                    self.repository.security_event(user.organization_id, user.user_id, "SESSIONS_REVOKED", target, {})
            self.store.audit_event(user.organization_id, user.user_id, "SESSIONS_REVOKED", f"user:{target}", target_user_id=target)
            return self._json(200, {"status":"sessions_revoked", "user_id":target})
        if method == "POST" and path == "/v1/organization/invitations":
            self._require_role(user, "OWNER", "ADMIN")
            body = self._body(environ)
            try:
                email = normalize_email(str(body.get("email", ""))); role = validate_role(str(body.get("role", "CLIENT")))
            except ValueError as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            if role == "OWNER" and user.role != "OWNER":
                raise APIError(403, "FORBIDDEN", "only an owner can invite an owner")
            from datetime import timedelta
            ttl = int(body.get("ttl_seconds", 7*24*3600))
            if ttl < 300 or ttl > 30*24*3600: raise APIError(422, "VALIDATION_ERROR", "invalid invitation ttl")
            token = secrets.token_urlsafe(32); token_hash = hash_token(token); expires = utc_now() + timedelta(seconds=ttl); iid=str(uuid.uuid4())
            row={"invitation_id":iid,"organization_id":user.organization_id,"email":email,"role":role,"expires_at":expires.isoformat(),"invited_by":user.user_id,"accepted_at":None,"revoked_at":None,"token_hash":token_hash}
            self.store.invitations[iid]=row
            if self.repository is not None and hasattr(self.repository, "create_invitation"):
                self.repository.create_invitation(user.organization_id,email,role,token_hash,user.user_id,expires.isoformat())
            self.store.audit_event(user.organization_id,user.user_id,"INVITATION_CREATED",f"invitation:{iid}",email=email,role=role)
            # Token is returned once to the caller; it is never persisted in clear text.
            return self._json(201,{k:v for k,v in row.items() if k != "token"}|{"invitation_token":token})
        if method == "GET" and path == "/v1/organization/members":
            rows=[{"user_id":u.user_id,"email":u.email,"role":u.role} for u in self.store.users.values() if u.organization_id==user.organization_id]
            return self._json(200,{"items":rows,"count":len(rows)})
        if method == "POST" and path.startswith("/v1/organization/members/") and path.endswith("/role"):
            self._require_role(user,"OWNER","ADMIN")
            target_id=path.split("/")[4]; body=self._body(environ); role=validate_role(str(body.get("role","")))
            target=self.store.users.get(target_id)
            if target is None or target.organization_id != user.organization_id: raise APIError(404,"NOT_FOUND","user not found")
            if role=="OWNER" and user.role!="OWNER": raise APIError(403,"FORBIDDEN","only an owner can assign owner")
            if target.role=="OWNER" and role!="OWNER" and user.role!="OWNER": raise APIError(403,"FORBIDDEN","only an owner can demote an owner")
            target=User(target.user_id,target.organization_id,target.email,target.password_hash,role); self.store.users[target.user_id]=target
            for th,sess in list(self.store.sessions.items()):
                if sess.user_id==target.user_id: self.store.sessions[th]=Session(sess.user_id,sess.organization_id,role,sess.token_hash,sess.expires_at,utc_now())
            if self.repository is not None and hasattr(self.repository,"update_role"): self.repository.update_role(user.organization_id,target.user_id,role)
            self.store.audit_event(user.organization_id,user.user_id,"ROLE_CHANGED",f"user:{target.user_id}",role=role)
            return self._json(200,{"user_id":target.user_id,"role":role})
        if method == "GET" and path == "/v1/organization/sla-calendar":
            return self._json(200, {"calendar": self.store.sla_calendars.get(user.organization_id, {"timezone":"UTC","workdays":[0,1,2,3,4,5,6],"start_hour":0,"end_hour":24,"holidays":[]}), "business_calendar_configured": user.organization_id in self.store.sla_calendars})
        if method == "POST" and path == "/v1/organization/sla-calendar":
            self._require_role(user, "OWNER", "ADMIN")
            body = self._body(environ)
            try:
                cal = calendar_from_dict(body)
            except (TypeError, ValueError) as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            payload = {"timezone":cal.timezone,"workdays":list(cal.workdays),"start_hour":cal.start_hour,"end_hour":cal.end_hour,"holidays":list(cal.holidays)}
            self.store.sla_calendars[user.organization_id] = payload
            if self.repository is not None and hasattr(self.repository, "upsert_sla_calendar"):
                self.repository.upsert_sla_calendar(user.organization_id, payload)
            self.store.audit_event(user.organization_id, user.user_id, "SLA_CALENDAR_UPDATED", f"organization:{user.organization_id}", calendar=payload)
            return self._json(200, {"calendar":payload})
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
            review = ReviewContext(rid, user.organization_id, str(body.get("location_id", "")), body.get("author_display_name"), rating, str(body["text"]), str(body.get("published_at", "")), body.get("updated_at"), body.get("language"), "GOOGLE", body.get("review_url"))
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
            if not review: raise APIError(404, "NOT_FOUND", "review not found")
            claims = extract_claims(review)
            signals = classify_policy_signals(claims)
            return self._json(200, {"review": asdict(review), "claims": [asdict(c) for c in claims], "policy_signals": [asdict(s) for s in signals]})
        if method == "POST" and path == "/v1/evidence":
            body = self._body(environ)
            case_id = str(body.get("case_id", ""))
            if not case_id or (user.organization_id, case_id) not in self.store.cases:
                raise APIError(404, "NOT_FOUND", "case not found")
            filename = str(body.get("filename", "")); content_type = str(body.get("content_type", "")); encoded = body.get("content_base64")
            if not filename or not isinstance(encoded, str):
                raise APIError(422, "VALIDATION_ERROR", "filename and content_base64 are required")
            try:
                content = base64.b64decode(encoded, validate=True)
            except Exception as exc:
                raise APIError(422, "VALIDATION_ERROR", "content_base64 is invalid") from exc
            evidence_id = str(uuid.uuid4())
            try:
                obj = self.store.vault.put(organization_id=user.organization_id, evidence_id=evidence_id, content=content, content_type=content_type, filename=filename)
            except (ValueError, PermissionError) as exc:
                raise APIError(422, "VALIDATION_ERROR", str(exc)) from exc
            raw_facts = body.get("facts", [])
            if raw_facts is None: raw_facts = []
            if not isinstance(raw_facts, list) or any(not isinstance(f, dict) for f in raw_facts):
                raise APIError(422, "VALIDATION_ERROR", "facts must be a list of objects")
            facts = []
            for f in raw_facts:
                key, kind, value = str(f.get("key", "")), str(f.get("kind", "")), str(f.get("value", ""))
                if not key or not kind or not value or len(key) > 200 or len(kind) > 80 or len(value) > 5000:
                    raise APIError(422, "VALIDATION_ERROR", "each fact requires bounded key, kind and value")
                facts.append({"fact_id": str(uuid.uuid4()), "evidence_id": evidence_id, "case_id": case_id, "organization_id": user.organization_id, "key": key, "kind": kind, "value": value, "source_location": str(f.get("source_location", "")), "verified": False, "verified_by": None, "verified_at": None})
            row = {"evidence_id": evidence_id, "organization_id": user.organization_id, "case_id": case_id, "filename": filename, "content_type": content_type, "size_bytes": obj.size_bytes, "sha256": obj.sha256, "object_key": obj.object_key, "verified": False, "created_by": user.user_id}
            self.store.evidence[(user.organization_id, evidence_id)] = row
            self.store.evidence_facts[(user.organization_id, evidence_id)] = facts
            if self.repository is not None:
                for fact in facts:
                    self.repository.put_evidence_fact(user.organization_id, fact)
            self.store.audit_event(user.organization_id, user.user_id, "EVIDENCE_UPLOADED", f"evidence:{evidence_id}", sha256=obj.sha256, case_id=case_id)
            row = dict(row); row["download_url"] = sign_download_url(object_key=obj.object_key, organization_id=user.organization_id, secret=self.store.download_secret)
            return self._json(201, {"evidence": row})
        if method == "GET" and path == "/v1/evidence":
            rows = [e for (org, _), e in self.store.evidence.items() if org == user.organization_id]
            return self._json(200, {"items": rows, "count": len(rows)})
        if method == "GET" and path.startswith("/v1/evidence/"):
            eid = path.rsplit("/", 1)[-1]
            row = self.store.evidence.get((user.organization_id, eid))
            if not row: raise APIError(404, "NOT_FOUND", "evidence not found")
            if not verify_integrity(self.store.vault.get(organization_id=user.organization_id, object_key=row["object_key"]), row["sha256"]):
                raise APIError(409, "INTEGRITY_FAILURE", "stored evidence integrity check failed")
            out = dict(row); out["download_url"] = sign_download_url(object_key=row["object_key"], organization_id=user.organization_id, secret=self.store.download_secret)
            return self._json(200, {"evidence": out})
        if method == "POST" and path.startswith("/v1/evidence/") and path.endswith("/verify") and len(path.split("/")) == 5:
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            eid = path.split("/")[3]; row = self.store.evidence.get((user.organization_id, eid))
            if not row: raise APIError(404, "NOT_FOUND", "evidence not found")
            if not verify_integrity(self.store.vault.get(organization_id=user.organization_id, object_key=row["object_key"]), row["sha256"]):
                raise APIError(409, "INTEGRITY_FAILURE", "stored evidence integrity check failed")
            row["verified"] = True; row["verified_by"] = user.user_id; row["verified_at"] = utc_now().isoformat()
            self.store.audit_event(user.organization_id, user.user_id, "EVIDENCE_VERIFIED", f"evidence:{eid}")
            return self._json(200, {"evidence": row})
        if method == "POST" and path.startswith("/v1/evidence/") and path.endswith("/facts/verify"):
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            eid = path.split("/")[3]; row = self.store.evidence.get((user.organization_id, eid))
            if not row: raise APIError(404, "NOT_FOUND", "evidence not found")
            if not row.get("verified"):
                raise APIError(409, "STATE_CONFLICT", "evidence must be verified before its facts can be verified")
            body = self._body(environ); fact_ids = body.get("fact_ids")
            facts = self.store.evidence_facts.get((user.organization_id, eid), [])
            if fact_ids is None: fact_ids = [f["fact_id"] for f in facts]
            if not isinstance(fact_ids, list): raise APIError(422, "VALIDATION_ERROR", "fact_ids must be a list")
            selected = set(str(x) for x in fact_ids)
            changed = 0
            for fact in facts:
                if fact["fact_id"] in selected:
                    fact["verified"] = True; fact["verified_by"] = user.user_id; fact["verified_at"] = utc_now().isoformat(); changed += 1
            if self.repository is not None:
                for fact in facts:
                    self.repository.put_evidence_fact(user.organization_id, fact)
            self.store.audit_event(user.organization_id, user.user_id, "EVIDENCE_FACTS_VERIFIED", f"evidence:{eid}", fact_ids=sorted(selected), count=changed)
            return self._json(200, {"facts": facts, "verified_count": changed})
        if method == "GET" and path == "/v1/review-queue":
            items = []
            for (org, cid), case in self.store.cases.items():
                if org != user.organization_id:
                    continue
                review = self.store.reviews.get((org, case.review_id))
                if review is None:
                    continue
                claims = extract_claims(review); signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get((org, cid), [])
                suggestions = self.store.fact_suggestions.get((org, cid), [])
                evidence_rows = [e for (eo, _), e in self.store.evidence.items() if eo == org and e.get("case_id") == cid]
                evidence = tuple(EvidenceView(e["evidence_id"], e["filename"], e.get("content_type") or "UNKNOWN", e["sha256"], "VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws = CaseWorkspace(cid, org, case.status, "NORMAL", ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
                    tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims),
                    tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals), evidence, (),
                    tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions))
                required = {c.claim_id: [] for c in claims}
                missing = missing_evidence_tasks(ws, required)
                item = score_case(case_id=cid, created_at=case.created_at, policy_statuses=[s.status for s in signals], contradiction_count=len(contradictions), missing_evidence_count=len(missing), unverified_suggestion_count=len([x for x in suggestions if not x.get("verified")]), assigned_to=case.assigned_to)
                payload = asdict(item)
                payload["sla"] = asdict(calculate_sla(priority=item.priority, created_at=case.created_at, paused_at=case.sla_paused_at, paused_seconds=case.sla_paused_seconds, calendar=self._calendar(user.organization_id)))
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
                claims = extract_claims(review); signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get((org, cid), [])
                suggestions = self.store.fact_suggestions.get((org, cid), [])
                evidence_rows = [e for (eo, _), e in self.store.evidence.items() if eo == org and e.get("case_id") == cid]
                evidence = tuple(EvidenceView(e["evidence_id"], e["filename"], e.get("content_type") or "UNKNOWN", e["sha256"], "VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws = CaseWorkspace(cid, org, case.status, "NORMAL", ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
                    tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims),
                    tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals), evidence, (),
                    tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions))
                missing = missing_evidence_tasks(ws, {c.claim_id: [] for c in claims})
                item = score_case(case_id=cid, created_at=case.created_at, policy_statuses=[s.status for s in signals], contradiction_count=len(contradictions), missing_evidence_count=len(missing), unverified_suggestion_count=len([x for x in suggestions if not x.get("verified")]), assigned_to=case.assigned_to)
                key = case.assigned_to or "UNASSIGNED"
                row = rows.setdefault(key, {"user_id": case.assigned_to, "case_count": 0, "priority_score_total": 0, "critical_count": 0, "high_count": 0, "overdue_count": 0, "due_soon_count": 0})
                row["case_count"] += 1; row["priority_score_total"] += item.priority_score
                if item.priority == "CRITICAL": row["critical_count"] += 1
                elif item.priority == "HIGH": row["high_count"] += 1
                sla = calculate_sla(priority=item.priority, created_at=case.created_at, paused_at=case.sla_paused_at, paused_seconds=case.sla_paused_seconds, calendar=self._calendar(user.organization_id))
                if sla.status == "OVERDUE": row["overdue_count"] += 1
                elif sla.status == "DUE_SOON": row["due_soon_count"] += 1
            items = sorted(rows.values(), key=lambda x: (-x["overdue_count"], -x["priority_score_total"], str(x["user_id"])))
            return self._json(200, {"items": items, "count": len(items)})
        if method == "POST" and path.startswith("/v1/review-queue/") and path.endswith("/claim"):
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            cid = path.split("/")[3]
            case = self.store.cases.get((user.organization_id, cid))
            if not case: raise APIError(404, "NOT_FOUND", "case not found")
            if case.assigned_to and case.assigned_to != user.user_id:
                raise APIError(409, "ALREADY_ASSIGNED", "case is already assigned")
            case.assigned_to = user.user_id
            self.store.case_assignments[(user.organization_id, cid)] = user.user_id
            if self.repository is not None:
                self.repository.assign_case(user.organization_id, cid, user.user_id)
            self.store.audit_event(user.organization_id, user.user_id, "CASE_ASSIGNED", f"case:{cid}", assignee_id=user.user_id)
            return self._json(200, {"case_id": cid, "assigned_to": user.user_id})
        if method == "POST" and path.startswith("/v1/review-queue/") and path.endswith("/unclaim"):
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            cid = path.split("/")[3]
            case = self.store.cases.get((user.organization_id, cid))
            if not case: raise APIError(404, "NOT_FOUND", "case not found")
            if case.assigned_to not in (None, user.user_id) and user.role not in {"OWNER", "ADMIN"}:
                raise APIError(403, "FORBIDDEN", "only the assignee or manager may unclaim")
            case.assigned_to = None
            self.store.case_assignments[(user.organization_id, cid)] = None
            if self.repository is not None:
                self.repository.assign_case(user.organization_id, cid, None)
            self.store.audit_event(user.organization_id, user.user_id, "CASE_UNASSIGNED", f"case:{cid}")
            return self._json(200, {"case_id": cid, "assigned_to": None})
        if method == "GET" and path == "/v1/escalations":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            items=[]
            for (org,cid), case in self.store.cases.items():
                if org != user.organization_id: continue
                review=self.store.reviews.get((org,case.review_id))
                if review is None: continue
                claims=extract_claims(review); signals=classify_policy_signals(claims); contradictions=self.store.contradictions.get((org,cid),[]); suggestions=self.store.fact_suggestions.get((org,cid),[])
                evidence_rows=[e for (eo,_),e in self.store.evidence.items() if eo==org and e.get("case_id")==cid]
                evidence=tuple(EvidenceView(e["evidence_id"],e["filename"],e.get("content_type") or "UNKNOWN",e["sha256"],"VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws=CaseWorkspace(cid,org,case.status,"NORMAL",ReviewSummary(review.review_id,review.rating,review.text,review.published_at),tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims),tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals),evidence,(),tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions))
                missing=missing_evidence_tasks(ws,{c.claim_id:[] for c in claims})
                item=score_case(case_id=cid,created_at=case.created_at,policy_statuses=[s.status for s in signals],contradiction_count=len(contradictions),missing_evidence_count=len(missing),unverified_suggestion_count=len([x for x in suggestions if not x.get("verified")]),assigned_to=case.assigned_to)
                sla=calculate_sla(priority=item.priority,created_at=case.created_at,paused_at=case.sla_paused_at,paused_seconds=case.sla_paused_seconds,calendar=self._calendar(org))
                esc=self._escalation_for(org,cid,sla)
                if esc: items.append(esc.payload() | {"sla":asdict(sla),"assigned_to":case.assigned_to})
            return self._json(200,{"items":items,"count":len(items)})
        if method == "POST" and path.startswith("/v1/escalations/") and path.endswith("/acknowledge"):
            self._require_role(user,"OWNER","ADMIN","ANALYST")
            parts=path.split("/"); cid=parts[3]; level=str(self._body(environ).get("level","DUE")); esc=self.store.escalations.get((user.organization_id,cid,level))
            if esc is None: raise APIError(404,"NOT_FOUND","escalation not found")
            if esc.status == "RESOLVED": raise APIError(409,"STATE_CONFLICT","escalation is already resolved")
            esc.status="ACKNOWLEDGED"; esc.acknowledged_by=user.user_id; esc.acknowledged_at=utc_now().isoformat()
            if self.repository is not None and hasattr(self.repository,"upsert_escalation"): self.repository.upsert_escalation(user.organization_id,esc.payload())
            self.store.audit_event(user.organization_id,user.user_id,"ESCALATION_ACKNOWLEDGED",f"case:{cid}",level=level)
            return self._json(200,{"escalation":esc.payload()})
        if method == "POST" and path.startswith("/v1/escalations/") and path.endswith("/resolve"):
            self._require_role(user,"OWNER","ADMIN","ANALYST")
            parts=path.split("/"); cid=parts[3]; level=str(self._body(environ).get("level","DUE")); esc=self.store.escalations.get((user.organization_id,cid,level))
            if esc is None: raise APIError(404,"NOT_FOUND","escalation not found")
            if esc.status == "RESOLVED": raise APIError(409,"STATE_CONFLICT","escalation is already resolved")
            esc.status="RESOLVED"; esc.resolved_by=user.user_id; esc.resolved_at=utc_now().isoformat()
            if self.repository is not None and hasattr(self.repository,"upsert_escalation"): self.repository.upsert_escalation(user.organization_id,esc.payload())
            self.store.audit_event(user.organization_id,user.user_id,"ESCALATION_RESOLVED",f"case:{cid}",level=level)
            return self._json(200,{"escalation":esc.payload()})
        if method == "GET" and path == "/v1/organization/notification-policy":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            policy = self._notification_policy(user.organization_id)
            return self._json(200, {"policy": policy.payload(), "configured": user.organization_id in self.store.notification_policies})
        if method == "POST" and path == "/v1/organization/notification-policy":
            self._require_role(user, "OWNER", "ADMIN")
            try:
                policy = validate_policy(user.organization_id, self._body(environ))
            except ValueError as exc:
                raise APIError(400, "INVALID_NOTIFICATION_POLICY", str(exc))
            self.store.notification_policies[user.organization_id] = policy
            if self.repository is not None and hasattr(self.repository, "upsert_notification_policy"):
                self.repository.upsert_notification_policy(user.organization_id, policy.payload())
            self.store.audit_event(user.organization_id, user.user_id, "NOTIFICATION_POLICY_UPDATED", f"organization:{user.organization_id}", policy=policy.payload())
            return self._json(200, {"policy": policy.payload()})
        if method == "POST" and path == "/v1/notifications/worker/run":
            self._require_role(user, "OWNER", "ADMIN")
            body = self._body(environ)
            try:
                limit = int(body.get("limit", 25))
            except (TypeError, ValueError):
                raise APIError(400, "INVALID_LIMIT", "limit must be an integer")
            if self.repository is not None and hasattr(self.repository, "list_notifications"):
                rows = self.repository.list_notifications(user.organization_id, "PENDING")
                for row in rows:
                    n = Notification(**row); self.store.notifications[(user.organization_id, n.notification_id)] = n
            notifications = [n for (org, _), n in self.store.notifications.items() if org == user.organization_id]
            def persist(n):
                if self.repository is not None and hasattr(self.repository, "update_notification"):
                    self.repository.update_notification(user.organization_id, n.payload())
            self.notification_worker.policy = self._notification_policy(user.organization_id)
            result = self.notification_worker.run_once(
                notifications, organization_id=user.organization_id, limit=limit, actor_id=user.user_id,
                persist=persist, audit=self.store.audit_event
            )
            self.store.audit_event(user.organization_id, user.user_id, "NOTIFICATION_WORKER_RUN", "notifications", processed=result.processed, sent=result.sent, retried=result.retried, dead_lettered=result.dead_lettered, skipped=result.skipped)
            return self._json(200, {"result": asdict(result)})
        if method == "GET" and path == "/v1/notifications":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            status_filter = parse_qs(environ.get("QUERY_STRING", "")).get("status", [None])[0]
            if self.repository is not None and hasattr(self.repository, "list_notifications"):
                rows = self.repository.list_notifications(user.organization_id, status_filter)
                for row in rows:
                    n = Notification(**row); self.store.notifications[(user.organization_id, n.notification_id)] = n
            items = [n.payload() for (org, _), n in self.store.notifications.items() if org == user.organization_id and (status_filter is None or n.status == status_filter)]
            items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
            return self._json(200, {"items": items, "count": len(items)})
        if method == "GET" and path == "/v1/notifications/metrics":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            if self.repository is not None and hasattr(self.repository, "list_notifications"):
                rows = self.repository.list_notifications(user.organization_id, None)
                for row in rows:
                    n = Notification(**row); self.store.notifications[(user.organization_id, n.notification_id)] = n
            metrics = build_notification_metrics(self.store.notifications.values(), self.store.audit, organization_id=user.organization_id)
            return self._json(200, {"metrics": metrics})
        if method == "POST" and path.startswith("/v1/escalations/") and path.endswith("/notify"):
            self._require_role(user, "OWNER", "ADMIN")
            parts = path.split("/"); cid = parts[3]; body = self._body(environ)
            level = str(body.get("level", "DUE")); channel = str(body.get("channel", "IN_APP")); target = str(body.get("target", user.user_id))
            esc = self.store.escalations.get((user.organization_id, cid, level))
            if esc is None: raise APIError(404, "NOT_FOUND", "escalation not found")
            if esc.status == "RESOLVED": raise APIError(409, "STATE_CONFLICT", "resolved escalation cannot be notified")
            allowed, reason = evaluate(self._notification_policy(user.organization_id), level=level, channel=channel, now=utc_now())
            if not allowed:
                self.store.audit_event(user.organization_id, user.user_id, "ESCALATION_NOTIFICATION_BLOCKED", f"case:{cid}", level=level, channel=channel, reason=reason)
                raise APIError(403, "NOTIFICATION_POLICY_BLOCKED", reason)
            try:
                notification = create_notification(organization_id=user.organization_id, case_id=cid, level=level, channel=channel, target=target, subject=str(body.get("subject", f"Review Defense escalation: {level}")), body=str(body.get("body", esc.reason)), actor_id=user.user_id)
            except ValueError as exc:
                raise APIError(400, "INVALID_NOTIFICATION", str(exc))
            key=(user.organization_id, notification.dedupe_key)
            for (_, _), existing in self.store.notifications.items():
                if existing.organization_id == user.organization_id and existing.dedupe_key == notification.dedupe_key and existing.status == "PENDING":
                    return self._json(200, {"notification": existing.payload(), "deduplicated": True})
            self.store.notifications[(user.organization_id, notification.notification_id)] = notification
            if self.repository is not None and hasattr(self.repository, "create_notification"):
                self.repository.create_notification(user.organization_id, notification.payload())
            self.store.audit_event(user.organization_id, user.user_id, "ESCALATION_NOTIFICATION_QUEUED", f"case:{cid}", notification_id=notification.notification_id, level=level, channel=notification.channel)
            return self._json(201, {"notification": notification.payload(), "deduplicated": False})
        if method == "POST" and path.startswith("/v1/notifications/") and path.endswith("/cancel"):
            self._require_role(user, "OWNER", "ADMIN")
            nid = path.split("/")[3]; notification = self.store.notifications.get((user.organization_id, nid))
            if notification is None and self.repository is not None and hasattr(self.repository, "get_notification"):
                row = self.repository.get_notification(user.organization_id, nid)
                if row: notification = Notification(**row); self.store.notifications[(user.organization_id, nid)] = notification
            if notification is None: raise APIError(404, "NOT_FOUND", "notification not found")
            if notification.status != "PENDING": raise APIError(409, "STATE_CONFLICT", "only pending notifications can be cancelled")
            notification.status = "CANCELLED"; notification.cancelled_by = user.user_id; notification.cancelled_at = utc_now().isoformat()
            if self.repository is not None and hasattr(self.repository, "update_notification"):
                self.repository.update_notification(user.organization_id, notification.payload())
            self.store.audit_event(user.organization_id, user.user_id, "ESCALATION_NOTIFICATION_CANCELLED", f"case:{notification.case_id}", notification_id=nid)
            return self._json(200, {"notification": notification.payload()})
        if method == "POST" and path.startswith("/v1/notifications/") and path.endswith("/deliver"):
            self._require_role(user, "OWNER", "ADMIN")
            nid = path.split("/")[3]
            notification = self.store.notifications.get((user.organization_id, nid))
            if notification is None and self.repository is not None and hasattr(self.repository, "get_notification"):
                row = self.repository.get_notification(user.organization_id, nid)
                if row:
                    notification = Notification(**row); self.store.notifications[(user.organization_id, nid)] = notification
            if notification is None: raise APIError(404, "NOT_FOUND", "notification not found")
            body = self._body(environ)
            allowed, reason = evaluate(self._notification_policy(user.organization_id), level=notification.escalation_level, channel=notification.channel, now=utc_now())
            if not allowed:
                self.store.audit_event(user.organization_id, user.user_id, "ESCALATION_NOTIFICATION_BLOCKED", f"case:{notification.case_id}", notification_id=nid, reason=reason)
                raise APIError(403, "NOTIFICATION_POLICY_BLOCKED", reason)
            try:
                result = self.delivery_func(notification, email_config=self.delivery_email_config)
            except DeliveryError as exc:
                notification.delivery_attempts = getattr(notification, "delivery_attempts", 0) + 1
                notification.last_attempt_at = utc_now().isoformat()
                notification.delivery_error = str(exc)
                if self.repository is not None and hasattr(self.repository, "record_notification_attempt"):
                    self.repository.record_notification_attempt(user.organization_id, notification.payload())
                self.store.audit_event(user.organization_id, user.user_id, "ESCALATION_NOTIFICATION_DELIVERY_FAILED", f"case:{notification.case_id}", notification_id=nid, channel=notification.channel, error=str(exc))
                return self._json(502, {"error":{"code":"DELIVERY_FAILED","message":str(exc)},"notification":notification.payload()})
            notification.status = "SENT"; notification.sent_by = user.user_id; notification.sent_at = utc_now().isoformat()
            notification.delivery_attempts = getattr(notification, "delivery_attempts", 0) + 1
            notification.last_attempt_at = utc_now().isoformat(); notification.delivery_error = None
            if self.repository is not None and hasattr(self.repository, "update_notification"):
                self.repository.update_notification(user.organization_id, notification.payload())
            self.store.audit_event(user.organization_id, user.user_id, "ESCALATION_NOTIFICATION_DELIVERED", f"case:{notification.case_id}", notification_id=nid, channel=notification.channel, provider=result.provider)
            return self._json(200, {"notification": notification.payload(), "delivery": result.__dict__})
        if method == "POST" and path.startswith("/v1/notifications/") and path.endswith("/mark-sent"):
            self._require_role(user, "OWNER", "ADMIN")
            nid = path.split("/")[3]; notification = self.store.notifications.get((user.organization_id, nid))
            if notification is None and self.repository is not None and hasattr(self.repository, "get_notification"):
                row = self.repository.get_notification(user.organization_id, nid)
                if row: notification = Notification(**row); self.store.notifications[(user.organization_id, nid)] = notification
            if notification is None: raise APIError(404, "NOT_FOUND", "notification not found")
            if notification.status != "PENDING": raise APIError(409, "STATE_CONFLICT", "only pending notifications can be marked sent")
            notification.status = "SENT"; notification.sent_by = user.user_id; notification.sent_at = utc_now().isoformat()
            if self.repository is not None and hasattr(self.repository, "update_notification"):
                self.repository.update_notification(user.organization_id, notification.payload())
            self.store.audit_event(user.organization_id, user.user_id, "ESCALATION_NOTIFICATION_MARKED_SENT", f"case:{notification.case_id}", notification_id=nid)
            return self._json(200, {"notification": notification.payload()})
        if method == "GET" and path == "/v1/approvals":
            rows = [asdict(a) for a in self.store.approvals if a.organization_id == user.organization_id]
            return self._json(200, {"items": rows, "count": len(rows)})
        if method == "GET" and path == "/v1/submissions":
            rows = [s for (org, _), s in self.store.submissions.items() if org == user.organization_id]
            return self._json(200, {"items": rows, "count": len(rows)})
        if method == "POST" and path == "/v1/cases":
            self._require_role(user, "OWNER", "ADMIN", "ANALYST")
            body = self._body(environ); rid = str(body.get("review_id", ""))
            if (user.organization_id, rid) not in self.store.reviews:
                raise APIError(404, "NOT_FOUND", "review not found")
            def create():
                cid = str(uuid.uuid4()); case = Case(cid, user.organization_id, rid, "ANALYZING", created_at=utc_now().isoformat())
                self.store.cases[(user.organization_id, cid)] = case
                if self.repository is not None:
                    self.repository.create_case_persistent(user.organization_id, cid, rid, case.status, user.user_id)
                self.store.audit_event(user.organization_id, user.user_id, "CASE_CREATED", f"case:{cid}", review_id=rid)
                return {"case": asdict(case)}
            return self._json(201, self._idem(user, environ, body, create))
        if method == "GET" and path == "/v1/cases":
            rows = [c for (org, _), c in self.store.cases.items() if org == user.organization_id]
            return self._json(200, {"items": [asdict(c) for c in rows], "count": len(rows)})
        if path.startswith("/v1/cases/"):
            parts = path.split("/")
            if len(parts) < 4: raise APIError(404, "NOT_FOUND", "resource not found")
            cid = parts[3]; case = self.store.cases.get((user.organization_id, cid))
            if not case: raise APIError(404, "NOT_FOUND", "case not found")
            if method == "GET" and len(parts) == 4:
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review); signals = classify_policy_signals(claims)
                return self._json(200, {"case": asdict(case), "review": asdict(review), "claims": [asdict(c) for c in claims], "policy_signals": [asdict(s) for s in signals]})
            if method == "GET" and len(parts) == 5 and parts[4] == "workspace":
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review)
                signals = classify_policy_signals(claims)
                evidence_rows = [e for (org, _), e in self.store.evidence.items() if org == user.organization_id and e["case_id"] == cid]
                evidence = tuple(EvidenceView(e["evidence_id"], e["filename"], e.get("content_type") or "UNKNOWN", e["sha256"], "VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                claim_views = tuple(ClaimView(c.claim_id, c.text, c.claim_type, "UNVERIFIED") for c in claims)
                policy_views = tuple(PolicySignalView(s.code, s.status, s.justification) for s in signals)
                timeline_rows = [a for a in self.store.audit if a["organization_id"] == user.organization_id and (a["resource"] == f"case:{cid}" or a["resource"].startswith("evidence:") and a.get("meta", {}).get("case_id") == cid)]
                timeline = tuple(TimelineEvent(a["event_id"], a["at"], a["action"], a.get("actor_id") or "system", "AUDIT") for a in timeline_rows)
                required = {}
                for signal in signals:
                    for claim_id in signal.claim_ids:
                        required.setdefault(claim_id, []).extend(signal.evidence_required)
                tasks = missing_evidence_tasks(CaseWorkspace(
                    cid, user.organization_id, case.status, "HIGH" if signals else "NORMAL",
                    ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
                    claim_views, policy_views, evidence, timeline, (), 0.0
                ), required)
                coverage = 1.0 if not tasks else max(0.0, len({t.evidence_requirement for t in tasks if t.status != "OPEN"}) / max(1, len({r for rs in required.values() for r in rs})))
                stored_contradictions = self.store.contradictions.get((user.organization_id, cid), [])
                contradiction_views = tuple(Contradiction(c["contradiction_id"], c["description"], c["claim_id"], tuple(c["evidence_ids"]), bool(c.get("requires_human_review", True))) for c in stored_contradictions)
                workspace = CaseWorkspace(
                    cid, user.organization_id, case.status, "HIGH" if signals or contradiction_views else "NORMAL",
                    ReviewSummary(review.review_id, review.rating, review.text, review.published_at),
                    claim_views, policy_views, evidence, timeline, contradiction_views, coverage
                )
                return self._json(200, {
                    "workspace": asdict(workspace),
                    "evidence_tasks": [asdict(t) for t in tasks],
                    "requires_human_review": case_requires_human_review(workspace),
                    "decision": asdict(self.store.decisions[(user.organization_id, case.decision_id)]) if case.decision_id and (user.organization_id, case.decision_id) in self.store.decisions else None,
                    "snapshot": asdict(self.store.snapshots[(user.organization_id, cid)]) if (user.organization_id, cid) in self.store.snapshots else None,
                    "approvals": [asdict(a) for a in self.store.approvals if a.organization_id == user.organization_id and a.decision_id == case.decision_id],
                    "fact_suggestions": [s for (org, _), rows in self.store.fact_suggestions.items() if org == user.organization_id for s in rows if self.store.evidence.get((org, s["evidence_id"]), {}).get("case_id") == cid],
                })
            if method == "POST" and len(parts) == 5 and parts[4] == "pause-sla":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                if case.sla_paused_at:
                    raise APIError(409, "STATE_CONFLICT", "SLA is already paused")
                body = self._body(environ)
                reason = str(body.get("reason", "")).strip()
                if not reason or len(reason) > 500:
                    raise APIError(422, "VALIDATION_ERROR", "reason is required and must be at most 500 characters")
                case.sla_paused_at = utc_now().isoformat(); case.sla_pause_reason = reason
                if self.repository is not None:
                    self.repository.update_case_sla(user.organization_id, cid, paused_at=case.sla_paused_at, paused_seconds=case.sla_paused_seconds, pause_reason=reason)
                self.store.audit_event(user.organization_id, user.user_id, "CASE_SLA_PAUSED", f"case:{cid}", reason=reason)
                return self._json(200, {"case_id": cid, "sla_paused_at": case.sla_paused_at, "reason": reason})
            if method == "POST" and len(parts) == 5 and parts[4] == "resume-sla":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                if not case.sla_paused_at:
                    raise APIError(409, "STATE_CONFLICT", "SLA is not paused")
                paused_at = __import__("datetime").datetime.fromisoformat(case.sla_paused_at.replace("Z", "+00:00"))
                if paused_at.tzinfo is None: paused_at = paused_at.replace(tzinfo=__import__("datetime").timezone.utc)
                now_dt = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                case.sla_paused_seconds += self._calendar(user.organization_id).business_seconds_between(paused_at, now_dt)
                case.sla_paused_at = None; case.sla_pause_reason = None
                if self.repository is not None:
                    self.repository.update_case_sla(user.organization_id, cid, paused_at=None, paused_seconds=case.sla_paused_seconds, pause_reason=None)
                self.store.audit_event(user.organization_id, user.user_id, "CASE_SLA_RESUMED", f"case:{cid}", paused_seconds=round(case.sla_paused_seconds, 2))
                return self._json(200, {"case_id": cid, "sla_paused_seconds": round(case.sla_paused_seconds, 2)})
            if method == "GET" and len(parts) == 5 and parts[4] == "sla":
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review); signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get((user.organization_id, cid), [])
                suggestions = self.store.fact_suggestions.get((user.organization_id, cid), [])
                evidence_rows = [e for (eo, _), e in self.store.evidence.items() if eo == user.organization_id and e.get("case_id") == cid]
                evidence = tuple(EvidenceView(e["evidence_id"], e["filename"], e.get("content_type") or "UNKNOWN", e["sha256"], "VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws = CaseWorkspace(cid, user.organization_id, case.status, "NORMAL", ReviewSummary(review.review_id, review.rating, review.text, review.published_at), tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims), tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals), evidence, (), tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions))
                missing = missing_evidence_tasks(ws, {c.claim_id: [] for c in claims})
                item = score_case(case_id=cid, created_at=case.created_at, policy_statuses=[s.status for s in signals], contradiction_count=len(contradictions), missing_evidence_count=len(missing), unverified_suggestion_count=len([x for x in suggestions if not x.get("verified")]), assigned_to=case.assigned_to)
                sla = calculate_sla(priority=item.priority, created_at=case.created_at, paused_at=case.sla_paused_at, paused_seconds=case.sla_paused_seconds, calendar=self._calendar(user.organization_id))
                return self._json(200, {"case_id": cid, "sla": asdict(sla), "pause_reason": case.sla_pause_reason})
            if method == "POST" and len(parts) == 5 and parts[4] == "contradictions":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review)
                body = self._body(environ)
                requested_eids = body.get("evidence_ids")
                if requested_eids is not None and not isinstance(requested_eids, list):
                    raise APIError(422, "VALIDATION_ERROR", "evidence_ids must be a list")
                selected = set(str(x) for x in requested_eids) if requested_eids is not None else {eid for (org, eid), e in self.store.evidence.items() if org == user.organization_id and e["case_id"] == cid}
                facts: list[EvidenceFact] = []
                for eid in sorted(selected):
                    e = self.store.evidence.get((user.organization_id, eid))
                    if not e or e["case_id"] != cid:
                        continue
                    for f in self.store.evidence_facts.get((user.organization_id, eid), []):
                        facts.append(EvidenceFact(eid, f["key"], f["kind"], f["value"], f.get("source_location", ""), bool(f.get("verified"))))
                findings = detect_contradictions(organization_id=user.organization_id, case_id=cid, claims=claims, evidence_facts=facts)
                rows = [asdict(f) for f in findings]
                self.store.contradictions[(user.organization_id, cid)] = rows
                if self.repository is not None:
                    for finding in rows:
                        self.repository.put_contradiction(user.organization_id, finding)
                self.store.audit_event(user.organization_id, user.user_id, "CONTRADICTIONS_ANALYZED", f"case:{cid}", contradiction_count=len(rows), evidence_ids=sorted(selected))
                return self._json(200, {"contradictions": rows, "count": len(rows), "requires_human_review": bool(rows)})
            if method == "POST" and len(parts) == 5 and parts[4] == "extract-facts":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                body = self._body(environ)
                requested = body.get("evidence_ids")
                if requested is not None and not isinstance(requested, list):
                    raise APIError(422, "VALIDATION_ERROR", "evidence_ids must be a list")
                selected = [str(x) for x in requested] if requested is not None else [eid for (org, eid), e in self.store.evidence.items() if org == user.organization_id and e["case_id"] == cid]
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
                        # Unsupported/unreadable evidence remains available for manual review;
                        # extraction failure must never become a false fact.
                        self.store.audit_event(user.organization_id, user.user_id, "EVIDENCE_TEXT_EXTRACTION_FAILED", f"evidence:{eid}", case_id=cid, reason=str(exc)[:240])
                        continue
                    suggestions = [asdict(x) for x in extract_text_fact_suggestions(evidence_id=eid, content=extracted.text.encode("utf-8"), content_type="text/plain")]
                    for suggestion in suggestions:
                        suggestion["case_id"] = cid
                        suggestion["extraction_method"] = extracted.method
                        if self.repository is not None:
                            self.repository.put_fact_suggestion(user.organization_id, suggestion)
                    self.store.fact_suggestions[(user.organization_id, eid)] = suggestions
                    all_suggestions.extend(suggestions)
                    self.store.audit_event(user.organization_id, user.user_id, "EVIDENCE_TEXT_EXTRACTED", f"evidence:{eid}", case_id=cid, method=extracted.method, character_count=len(extracted.text), suggestion_count=len(suggestions))
                self.store.audit_event(user.organization_id, user.user_id, "EVIDENCE_FACTS_SUGGESTED", f"case:{cid}", suggestion_count=len(all_suggestions), evidence_ids=selected)
                return self._json(200, {"suggestions": all_suggestions, "count": len(all_suggestions), "requires_human_review": bool(all_suggestions), "verified": False})
            if method == "GET" and len(parts) == 5 and parts[4] == "review-checklist":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST", "CLIENT", "VIEWER")
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = extract_claims(review); signals = classify_policy_signals(claims)
                contradictions = self.store.contradictions.get((user.organization_id, cid), [])
                suggestions = self.store.fact_suggestions.get((user.organization_id, cid), [])
                evidence_rows = [e for (org, _), e in self.store.evidence.items() if org == user.organization_id and e.get("case_id") == cid]
                required = {}
                for signal in signals:
                    for claim_id in signal.claim_ids:
                        required.setdefault(claim_id, []).extend(signal.evidence_required)
                evidence = tuple(EvidenceView(e["evidence_id"], e["filename"], e.get("content_type") or "UNKNOWN", e["sha256"], "VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws = CaseWorkspace(cid, user.organization_id, case.status, "NORMAL", ReviewSummary(review.review_id, review.rating, review.text, review.published_at), tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims), tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals), evidence, (), tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions))
                missing = missing_evidence_tasks(ws, required)
                key=(user.organization_id,cid)
                if key not in self.store.review_checklists and self.repository is not None and hasattr(self.repository, "list_case_review_checklist"):
                    rows=self.repository.list_case_review_checklist(user.organization_id,cid)
                    self.store.review_checklists[key]=[dict(zip(("item_id","organization_id","case_id","code","label","required","completed","completed_by","completed_at","note"), r)) for r in rows]
                if key not in self.store.review_checklists:
                    self.store.review_checklists[key] = [asdict(x) for x in build_checklist(organization_id=user.organization_id, case_id=cid, has_policy_signals=bool(signals), contradiction_count=len(contradictions), unverified_fact_count=sum(1 for x in suggestions if not x.get("verified")), missing_evidence_count=len(missing))]
                    if self.repository is not None and hasattr(self.repository, "upsert_case_review_checklist"):
                        for x in self.store.review_checklists[key]: self.repository.upsert_case_review_checklist(user.organization_id, x)
                items=[ReviewChecklistItem(**x) for x in self.store.review_checklists[key]]
                readiness=assess_readiness(case_id=cid, organization_id=user.organization_id, items=items, contradiction_count=len(contradictions), unverified_fact_count=sum(1 for x in suggestions if not x.get("verified")), missing_evidence_count=len(missing))
                return self._json(200, {"items":[asdict(x) for x in items], "readiness":asdict(readiness)})
            if method == "POST" and len(parts) == 5 and parts[4] == "review-checklist":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                body=self._body(environ); code=str(body.get("code","")).strip(); completed=body.get("completed")
                if not code or not isinstance(completed,bool): raise APIError(422,"VALIDATION_ERROR","code and boolean completed are required")
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims=extract_claims(review); signals=classify_policy_signals(claims); contradictions=self.store.contradictions.get((user.organization_id,cid),[]); suggestions=self.store.fact_suggestions.get((user.organization_id,cid),[])
                required={}; [required.setdefault(cid2,[]).extend(s.evidence_required) for s in signals for cid2 in s.claim_ids]
                evidence_rows=[e for (org,_),e in self.store.evidence.items() if org==user.organization_id and e.get("case_id")==cid]
                evidence=tuple(EvidenceView(e["evidence_id"],e["filename"],e.get("content_type") or "UNKNOWN",e["sha256"],"VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws=CaseWorkspace(cid,user.organization_id,case.status,"NORMAL",ReviewSummary(review.review_id,review.rating,review.text,review.published_at),tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims),tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals),evidence,(),tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions))
                missing=missing_evidence_tasks(ws,required); key=(user.organization_id,cid)
                if key not in self.store.review_checklists:
                    self.store.review_checklists[key]=[asdict(x) for x in build_checklist(organization_id=user.organization_id,case_id=cid,has_policy_signals=bool(signals),contradiction_count=len(contradictions),unverified_fact_count=sum(1 for x in suggestions if not x.get("verified")),missing_evidence_count=len(missing))]
                row=next((x for x in self.store.review_checklists[key] if x["code"]==code),None)
                if row is None: raise APIError(404,"NOT_FOUND","checklist item not found")
                row["completed"]=completed; row["completed_by"]=user.user_id if completed else None; row["completed_at"]=utc_now().isoformat() if completed else None; row["note"]=str(body.get("note"))[:1000] if body.get("note") is not None else None
                if self.repository is not None and hasattr(self.repository, "upsert_case_review_checklist"):
                    self.repository.upsert_case_review_checklist(user.organization_id, row)
                self.store.audit_event(user.organization_id,user.user_id,"CASE_REVIEW_CHECKLIST_UPDATED",f"case:{cid}",code=code,completed=completed)
                return self._json(200,{"item":row})
            if method == "GET" and len(parts) == 5 and parts[4] == "review-readiness":
                # Same advisory checklist, exposed as a compact readiness contract.
                status, headers, body = self._json(200,{})
                # Reuse checklist logic by requiring the checklist endpoint through internal construction below.
                review=self.store.reviews[(user.organization_id,case.review_id)]; claims=extract_claims(review); signals=classify_policy_signals(claims); contradictions=self.store.contradictions.get((user.organization_id,cid),[]); suggestions=self.store.fact_suggestions.get((user.organization_id,cid),[])
                evidence_rows=[e for (org,_),e in self.store.evidence.items() if org==user.organization_id and e.get("case_id")==cid]; evidence=tuple(EvidenceView(e["evidence_id"],e["filename"],e.get("content_type") or "UNKNOWN",e["sha256"],"VERIFIED" if e.get("verified") else "UNVERIFIED") for e in evidence_rows)
                ws=CaseWorkspace(cid,user.organization_id,case.status,"NORMAL",ReviewSummary(review.review_id,review.rating,review.text,review.published_at),tuple(ClaimView(c.claim_id,c.text,c.claim_type,"UNVERIFIED") for c in claims),tuple(PolicySignalView(s.code,s.status,s.justification) for s in signals),evidence,(),tuple(Contradiction(c["contradiction_id"],c["description"],c["claim_id"],tuple(c["evidence_ids"]),True) for c in contradictions)); missing=missing_evidence_tasks(ws,{c.claim_id:[] for c in claims})
                key=(user.organization_id,cid)
                if key not in self.store.review_checklists: self.store.review_checklists[key]=[asdict(x) for x in build_checklist(organization_id=user.organization_id,case_id=cid,has_policy_signals=bool(signals),contradiction_count=len(contradictions),unverified_fact_count=sum(1 for x in suggestions if not x.get("verified")),missing_evidence_count=len(missing))]
                items=[ReviewChecklistItem(**x) for x in self.store.review_checklists[key]]; readiness=assess_readiness(case_id=cid,organization_id=user.organization_id,items=items,contradiction_count=len(contradictions),unverified_fact_count=sum(1 for x in suggestions if not x.get("verified")),missing_evidence_count=len(missing))
                return self._json(200,{"readiness":asdict(readiness),"human_review_required":True})
            if method == "GET" and len(parts) == 5 and parts[4] == "contradictions":
                rows = self.store.contradictions.get((user.organization_id, cid), [])
                out=[]
                for row in rows:
                    item=dict(row); item["disposition"]=self.store.contradiction_dispositions.get((user.organization_id,row["contradiction_id"]))
                    out.append(item)
                return self._json(200, {"contradictions": out, "count": len(out), "requires_human_review": bool(out)})
            if method == "GET" and len(parts) == 7 and parts[4] == "contradictions" and parts[6] == "history":
                contradiction_id=parts[5]
                rows=self.store.contradictions.get((user.organization_id,cid),[])
                if not any(x.get("contradiction_id")==contradiction_id for x in rows): raise APIError(404,"NOT_FOUND","contradiction not found")
                history=list(self.store.contradiction_disposition_history.get((user.organization_id,contradiction_id),[]))
                if self.repository is not None and hasattr(self.repository,"list_contradiction_disposition_history"):
                    try: history=self.repository.list_contradiction_disposition_history(user.organization_id,contradiction_id) or history
                    except Exception: pass
                return self._json(200,{"history":history,"count":len(history),"requires_human_review":True})
            if method == "GET" and len(parts) == 5 and parts[4] == "evidence-matrix":
                case=self.store.cases.get((user.organization_id,cid))
                if case is None: raise APIError(404,"NOT_FOUND","case not found")
                review=self.store.reviews.get((user.organization_id,case.review_id))
                if review is None: raise APIError(404,"NOT_FOUND","review not found")
                claims=extract_claims(review)
                evidence=list(self.store.evidence.values())
                evidence=[e for (o,_),e in self.store.evidence.items() if o==user.organization_id and e.get("case_id")==cid]
                contradictions=self.store.contradictions.get((user.organization_id,cid),[])
                dispositions=self.store.contradiction_dispositions
                matrix=build_evidence_matrix(claims=claims,evidence=evidence,contradictions=contradictions,dispositions=dispositions)
                return self._json(200,{"case_id":cid,"matrix":matrix,"count":len(matrix),"requires_human_review":True})
            if method == "GET" and len(parts) == 6 and parts[4] == "contradictions" and parts[5] in {x["contradiction_id"] for x in self.store.contradictions.get((user.organization_id,cid), [])}:
                contradiction_id=parts[5]
                row=next(x for x in self.store.contradictions[(user.organization_id,cid)] if x["contradiction_id"]==contradiction_id)
                return self._json(200,{"contradiction":row,"disposition":self.store.contradiction_dispositions.get((user.organization_id,contradiction_id))})
            if method == "POST" and len(parts) == 7 and parts[4] == "contradictions" and parts[6] == "disposition":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                contradiction_id=parts[5]
                rows=self.store.contradictions.get((user.organization_id,cid),[])
                if not any(x.get("contradiction_id")==contradiction_id for x in rows):
                    raise APIError(404,"NOT_FOUND","contradiction not found")
                body=self._body(environ)
                try:
                    disp=make_disposition(organization_id=user.organization_id,case_id=cid,contradiction_id=contradiction_id,status=body.get("status"),rationale=body.get("rationale"),actor_id=user.user_id,created_at=utc_now().isoformat())
                except ValueError as exc:
                    raise APIError(422,"VALIDATION_ERROR",str(exc))
                d=asdict(disp); self.store.contradiction_dispositions[(user.organization_id,contradiction_id)]=d
                hist=dict(d); hist["history_id"]="hist_"+__import__("hashlib").sha256(f"{d['disposition_id']}|{d['created_at']}".encode()).hexdigest()[:24]
                self.store.contradiction_disposition_history.setdefault((user.organization_id,contradiction_id),[]).append(hist)
                if self.repository is not None and hasattr(self.repository,"upsert_contradiction_disposition"):
                    self.repository.upsert_contradiction_disposition(user.organization_id,d)
                if self.repository is not None and hasattr(self.repository,"append_contradiction_disposition_history"):
                    self.repository.append_contradiction_disposition_history(user.organization_id,hist)
                self.store.audit_event(user.organization_id,user.user_id,"CONTRADICTION_DISPOSITIONED",f"case:{cid}",contradiction_id=contradiction_id,status=disp.status)
                return self._json(200,{"disposition":d,"requires_human_review":True})
            if method == "POST" and len(parts) == 5 and parts[4] == "decision":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                body = self._body(environ)
                kind = body.get("kind", "HUMAN_REVIEW"); rationale = str(body.get("rationale", ""))
                if not rationale.strip(): raise APIError(422, "VALIDATION_ERROR", "rationale is required")
                decision = create_decision(decision_id=str(uuid.uuid4()), case_id=cid, organization_id=user.organization_id, kind=kind, rationale=rationale, created_at=utc_now().isoformat(), created_by=user.user_id)
                self.store.decisions[(user.organization_id, decision.decision_id)] = decision
                if self.repository is not None:
                    self.repository.put_decision(user.organization_id, asdict(decision))
                case.decision_id = decision.decision_id; case.status = "ANALYZED"
                if self.repository is not None:
                    self.repository.update_case(user.organization_id, cid, status=case.status, decision_id=case.decision_id)
                self.store.audit_event(user.organization_id, user.user_id, "DECISION_CREATED", f"case:{cid}")
                return self._json(201, {"decision": asdict(decision)})
            if method == "POST" and len(parts) == 5 and parts[4] == "freeze":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                if not case.decision_id: raise APIError(409, "STATE_CONFLICT", "decision required before freeze")
                decision = self.store.decisions[(user.organization_id, case.decision_id)]
                review = self.store.reviews[(user.organization_id, case.review_id)]
                claims = [asdict(c) for c in extract_claims(review)]; signals = [asdict(s) for s in classify_policy_signals(extract_claims(review))]
                payload = {"case": asdict(case), "review": asdict(review), "claims": claims, "policy_signals": signals, "decision": asdict(decision)}
                snap = freeze_dossier(case_id=cid, organization_id=user.organization_id, payload=payload, frozen_at=utc_now().isoformat(), frozen_by=user.user_id)
                decision = attach_snapshot(decision, snap); decision = request_approval(decision)
                self.store.snapshots[(user.organization_id, cid)] = snap; self.store.decisions[(user.organization_id, case.decision_id)] = decision; case.snapshot_sha256 = snap.sha256; case.status = "HUMAN_REVIEW"
                if self.repository is not None:
                    self.repository.put_snapshot(user.organization_id, cid, snap.sha256, payload, user.user_id, snap.frozen_at)
                    self.repository.put_decision(user.organization_id, asdict(decision))
                    self.repository.update_case(user.organization_id, cid, status=case.status, snapshot_sha256=case.snapshot_sha256)
                self.store.audit_event(user.organization_id, user.user_id, "DOSSIER_FROZEN", f"case:{cid}", sha256=snap.sha256)
                return self._json(200, {"decision": asdict(decision), "snapshot_sha256": snap.sha256})
            if method == "POST" and len(parts) == 5 and parts[4] == "approve":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                if not case.decision_id or (user.organization_id, cid) not in self.store.snapshots: raise APIError(409, "STATE_CONFLICT", "frozen decision required")
                decision = self.store.decisions[(user.organization_id, case.decision_id)]; snap = self.store.snapshots[(user.organization_id, cid)]
                try:
                    approved, event = approve_decision(decision=decision, snapshot=snap, actor_id=user.user_id, actor_role=user.role, approval_id=str(uuid.uuid4()), approved_at=utc_now().isoformat())
                except (ValueError, PermissionError) as exc: raise APIError(409, "APPROVAL_REJECTED", str(exc)) from exc
                self.store.decisions[(user.organization_id, case.decision_id)] = approved; case.status = "READY_TO_SUBMIT"; self.store.approvals.append(event)
                if self.repository is not None:
                    self.repository.put_decision(user.organization_id, asdict(approved))
                    self.repository.put_approval(user.organization_id, asdict(event))
                    self.repository.update_case(user.organization_id, cid, status=case.status)
                self.store.audit_event(user.organization_id, user.user_id, "DECISION_APPROVED", f"case:{cid}")
                return self._json(200, {"decision": asdict(approved), "approval": asdict(event)})
            if method == "POST" and len(parts) == 5 and parts[4] == "submit":
                self._require_role(user, "OWNER", "ADMIN", "ANALYST")
                if not case.decision_id: raise APIError(409, "STATE_CONFLICT", "decision required")
                decision = self.store.decisions[(user.organization_id, case.decision_id)]
                if decision.status != "APPROVED": raise APIError(409, "APPROVAL_REQUIRED", "explicit human approval required before submission")
                body = self._body(environ)
                def submit():
                    sid = str(uuid.uuid4()); row = {"submission_id": sid, "case_id": cid, "organization_id": user.organization_id, "status": "DRAFT", "external_call": False}
                    self.store.submissions[(user.organization_id, sid)] = row
                    if self.repository is not None:
                        self.repository.put_submission(user.organization_id, row)
                    self.store.audit_event(user.organization_id, user.user_id, "SUBMISSION_PREPARED", f"submission:{sid}")
                    return {"submission": row}
                return self._json(201, self._idem(user, environ, body, submit))
            raise APIError(404, "NOT_FOUND", "case operation not found")
        if method == "POST" and path == "/v1/logout":
            header = environ.get("HTTP_AUTHORIZATION", ""); raw = header[7:].strip() if header.startswith("Bearer ") else ""
            th = __import__("hashlib").sha256(raw.encode()).hexdigest(); old = self.store.sessions.get(th)
            if old:
                self.store.sessions[th] = Session(old.user_id, old.organization_id, old.role, old.token_hash, old.expires_at, utc_now())
                if self.repository is not None:
                    self.repository.revoke_session(user.organization_id, th)
                    if hasattr(self.repository, "security_event"):
                        self.repository.security_event(user.organization_id, user.user_id, "LOGOUT", user.user_id, {"ip_hash": self._client_ip_hash(environ)})
                self.store.audit_event(user.organization_id, user.user_id, "LOGOUT", "session")
            return self._json(200, {"status": "logged_out"})
        raise APIError(404, "NOT_FOUND", "route not found")

    def __call__(self, environ, start_response):
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
            headers=[("Content-Type","text/html; charset=utf-8"),("Content-Length",str(len(body))),("X-Request-ID",trace_id)]
            if self.config.secure_headers:
                headers.extend(list(security_headers(production=self.config.production).items()))
            start_response("200 OK", headers)
            return [body]
        if path == "/robots.txt" and environ.get("REQUEST_METHOD") == "GET":
            body = robots()
            start_response("200 OK", [("Content-Type","text/plain; charset=utf-8"),("Content-Length",str(len(body))),("X-Request-ID",trace_id)])
            return [body]
        if path == "/sitemap.xml" and environ.get("REQUEST_METHOD") == "GET":
            body = sitemap()
            start_response("200 OK", [("Content-Type","application/xml; charset=utf-8"),("Content-Length",str(len(body))),("X-Request-ID",trace_id)])
            return [body]
        if path == "/" or path == "/app" or path == "/app/":
            path = "/index.html"
        if path == "/index.html" or path.startswith("/assets/"):
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
                elapsed = (_time.perf_counter() - started) * 1000
                self.telemetry.increment("http_requests_total", labels={"method": environ.get("REQUEST_METHOD", "GET"), "path": path, "status": "200"})
                self.telemetry.observe_ms("http_request_duration_ms", elapsed, labels={"method": environ.get("REQUEST_METHOD", "GET"), "path": path})
                start_response("200 OK", [("Content-Type", ctype), ("Content-Length", str(len(body))), ("X-Request-ID", trace_id)])
                return [body]
        try:
            status, headers, body = self.handle(environ)
        except APIError as exc:
            status, headers, body = self._json(exc.status, {"error": {"code": exc.code, "message": exc.message, "details": exc.details}})
        except Exception:
            status, headers, body = self._json(500, {"error": {"code": "INTERNAL_ERROR", "message": "internal server error"}})
        phrase = {200:"OK",201:"Created",400:"Bad Request",401:"Unauthorized",403:"Forbidden",404:"Not Found",409:"Conflict",413:"Payload Too Large",422:"Unprocessable Entity",429:"Too Many Requests",500:"Internal Server Error"}.get(status,"Error")
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
