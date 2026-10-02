"""V5.4 production observability primitives.

Framework-neutral telemetry for Review Defense: structured events, counters,
latency measurements, correlation IDs, redaction, immutable audit hash-chain,
and health/readiness checks. No network calls and no sensitive payload logging.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

SENSITIVE_KEYS = {
    "password", "passwd", "secret", "token", "access_token", "refresh_token",
    "authorization", "cookie", "set-cookie", "raw_review_text", "review_text",
    "content", "file_bytes", "evidence_bytes", "api_key", "private_key",
}
MAX_VALUE_LENGTH = 512


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_trace_id() -> str:
    return secrets.token_hex(16)


def new_span_id() -> str:
    return secrets.token_hex(8)


def _safe_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
        return value[:MAX_VALUE_LENGTH] + "…"
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return redact({str(k): v for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return [_safe_value(v) for v in value[:50]]
    return str(value)[:MAX_VALUE_LENGTH]


def redact(fields: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in fields.items():
        if key.lower() in SENSITIVE_KEYS:
            result[key] = "[REDACTED]"
        else:
            result[key] = _safe_value(value)
    return result


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    organization_id: str | None = None
    actor_id: str | None = None

    @classmethod
    def create(cls, *, organization_id: str | None = None, actor_id: str | None = None) -> "TraceContext":
        return cls(new_trace_id(), new_span_id(), organization_id, actor_id)


@dataclass(frozen=True)
class StructuredEvent:
    timestamp: str
    level: str
    event: str
    trace_id: str
    span_id: str
    organization_id: str | None
    actor_id: str | None
    fields: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp, "level": self.level, "event": self.event,
            "trace_id": self.trace_id, "span_id": self.span_id,
            "organization_id": self.organization_id, "actor_id": self.actor_id,
            "fields": redact(self.fields),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))


class InMemoryTelemetry:
    """Deterministic telemetry sink useful in tests and local development."""
    def __init__(self) -> None:
        self.events: list[StructuredEvent] = []
        self.counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = {}
        self.timings: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = {}
        self._lock = threading.Lock()

    def emit(self, *, event: str, level: str = "INFO", trace: TraceContext,
             fields: Mapping[str, Any] | None = None) -> StructuredEvent:
        item = StructuredEvent(utc_now().isoformat(), level.upper(), event,
                               trace.trace_id, trace.span_id, trace.organization_id,
                               trace.actor_id, redact(fields or {}))
        with self._lock:
            self.events.append(item)
        return item

    def increment(self, name: str, *, labels: Mapping[str, Any] | None = None, value: int = 1) -> int:
        key = (name, tuple(sorted((str(k), str(v)) for k, v in (labels or {}).items())))
        with self._lock:
            self.counters[key] = self.counters.get(key, 0) + value
            return self.counters[key]

    def observe_ms(self, name: str, milliseconds: float, *, labels: Mapping[str, Any] | None = None) -> None:
        if milliseconds < 0:
            raise ValueError("milliseconds must be non-negative")
        key = (name, tuple(sorted((str(k), str(v)) for k, v in (labels or {}).items())))
        with self._lock:
            self.timings.setdefault(key, []).append(float(milliseconds))

    def count_events(self, event: str) -> int:
        with self._lock:
            return sum(1 for item in self.events if item.event == event)

    def metric(self, name: str, *, labels: Mapping[str, Any] | None = None) -> int:
        key = (name, tuple(sorted((str(k), str(v)) for k, v in (labels or {}).items())))
        return self.counters.get(key, 0)

    def timing_stats(self, name: str, *, labels: Mapping[str, Any] | None = None) -> dict[str, float | int]:
        key = (name, tuple(sorted((str(k), str(v)) for k, v in (labels or {}).items())))
        values = self.timings.get(key, [])
        if not values:
            return {"count": 0, "avg_ms": 0.0, "max_ms": 0.0}
        return {"count": len(values), "avg_ms": sum(values) / len(values), "max_ms": max(values)}


class AuditChain:
    """Append-only audit records with a tamper-evident SHA-256 hash chain."""
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def append(self, *, organization_id: str, actor_id: str | None, action: str,
               resource_type: str, resource_id: str, trace_id: str,
               metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if not organization_id or not action or not resource_type or not resource_id:
            raise ValueError("audit identity fields are required")
        with self._lock:
            previous = self.records[-1]["hash"] if self.records else "GENESIS"
            record = {
                "sequence": len(self.records) + 1,
                "timestamp": utc_now().isoformat(),
                "organization_id": organization_id,
                "actor_id": actor_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "trace_id": trace_id,
                "metadata": redact(metadata or {}),
                "previous_hash": previous,
            }
            canonical = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
            record["hash"] = hashlib.sha256(canonical).hexdigest()
            self.records.append(record)
            return dict(record)

    def verify(self) -> bool:
        previous = "GENESIS"
        for expected_sequence, record in enumerate(self.records, 1):
            if record.get("sequence") != expected_sequence or record.get("previous_hash") != previous:
                return False
            candidate = dict(record)
            actual = candidate.pop("hash", None)
            canonical = json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode()
            expected = hashlib.sha256(canonical).hexdigest()
            if not actual or not hmac.compare_digest(actual, expected):
                return False
            previous = actual
        return True


def measure(operation: Callable[..., Any], telemetry: InMemoryTelemetry, *,
            metric_name: str, labels: Mapping[str, Any] | None = None) -> Callable[..., Any]:
    """Wrap an operation and emit duration/error metrics without swallowing errors."""
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = operation(*args, **kwargs)
            telemetry.increment(f"{metric_name}.success", labels=labels)
            return result
        except Exception as exc:
            telemetry.increment(f"{metric_name}.error", labels={**(labels or {}), "error": type(exc).__name__})
            raise
        finally:
            telemetry.observe_ms(metric_name, (time.perf_counter() - start) * 1000, labels=labels)
    return wrapped


@dataclass(frozen=True)
class HealthResult:
    status: str
    checks: Mapping[str, str]
    checked_at: str


def health_check(*, checks: Mapping[str, Callable[[], bool]]) -> HealthResult:
    results: dict[str, str] = {}
    overall = "ok"
    for name, fn in checks.items():
        try:
            results[name] = "ok" if fn() else "failed"
        except Exception:
            results[name] = "error"
        if results[name] != "ok":
            overall = "failed"
    return HealthResult(overall, results, utc_now().isoformat())


def readiness_check(*, checks: Mapping[str, Callable[[], bool]]) -> HealthResult:
    return health_check(checks=checks)
