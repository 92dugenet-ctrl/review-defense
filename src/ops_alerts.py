"""V6.29 bounded operational alert evaluation.

Pure, deterministic alert rules over in-process telemetry. No network calls,
no automatic remediation, and no external notifications are performed here.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class Alert:
    name: str
    severity: str
    status: str
    description: str


def evaluate_alerts(*, counters: Mapping[tuple[str, tuple[tuple[str,str],...]], int], readiness_ok: bool) -> list[Alert]:
    errors = sum(v for (name, _), v in counters.items() if name == "http_errors_total")
    requests = sum(v for (name, _), v in counters.items() if name == "http_requests_total")
    alerts = [Alert("service_not_ready", "critical", "firing" if not readiness_ok else "ok", "Application readiness check is failing.")]
    error_ratio = errors / requests if requests else 0.0
    alerts.append(Alert("http_5xx_ratio", "warning", "firing" if error_ratio >= 0.05 and requests >= 20 else "ok", "HTTP 5xx ratio is at or above 5% over the observed process lifetime."))
    return alerts
