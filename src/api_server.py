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


class ReviewDefenseAPI:
    """Small WSGI API with explicit human-gated state transitions."""
    def __init__(self, store: MemoryStore | None = None, *, session_ttl: int = 3600,
                 limiter: RateLimiter | None = None, repository=None, delivery_email_config: dict[str, Any] | None = None, delivery_func=deliver, config: ProductionConfig | None = None):
        self.store = store or MemoryStore()
        self.config = config or ProductionConfig.from_env()
        self.config.validate_startup(require_database=(repository is not None))
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
        path = urlsplit(environ.get("PATH_INFO", "/")).path
        if path == "/sitemap.xml":
            body = sitemap()
            start_response("200 OK", [("Content-Type","application/xml; charset=utf-8"),("Content-Length",str(len(body))),("X-Request-ID",trace_id)])
            return [body]
        if path == "/robots.txt":
            body = robots()
            start_response("200 OK", [("Content-Type","text/plain; charset=utf-8"),("Content-Length",str(len(body))),("X-Request-ID",trace_id)])
            return [body]
        if path.startswith("/") and is_seo_path(path) and environ.get("REQUEST_METHOD") == "GET":
            body = render_page(path)
            start_response("200 OK", [("Content-Type","text/html; charset=utf-8"),("Content-Length",str(len(body))),("X-Request-ID",trace_id)])
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
    return ReviewDefenseAPI(store=store, repository=repository, config=config)


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    from wsgiref.simple_server import make_server
    app = create_app()
    with make_server(host, port, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    serve()
