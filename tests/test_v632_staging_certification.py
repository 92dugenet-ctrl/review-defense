from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("staging_cert", ROOT / "scripts/staging_certification.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def test_staging_contract_is_complete():
    checks = mod.contract_checks()
    assert checks["all"] is True
    assert checks["postgres_healthcheck"]
    assert checks["migrations_before_app"]
    assert checks["tls_caddy"]
    assert checks["secure_headers"]


def test_live_requires_https():
    try:
        mod.live_checks("http://staging.example")
    except ValueError as e:
        assert "HTTPS" in str(e)
    else:
        raise AssertionError("HTTP staging URL must be rejected")


def test_live_metrics_are_not_public_contract(monkeypatch):
    calls = []
    def fake_fetch(base, path):
        calls.append(path)
        if path == "/health": return 200, {"version": "6.40", "service": "review-defense"}, {"content-security-policy":"x", "x-content-type-options":"nosniff", "x-frame-options":"DENY", "referrer-policy":"no-referrer"}
        if path == "/ready": return 200, {"status":"ready"}, {}
        raise RuntimeError("metrics should be represented by HTTPError in real runtime")
    monkeypatch.setattr(mod, "fetch", fake_fetch)
    try:
        mod.live_checks("https://staging.example")
    except RuntimeError as e:
        assert "metrics" in str(e)
    else:
        raise AssertionError("unexpectedly certified without protected metrics response")
