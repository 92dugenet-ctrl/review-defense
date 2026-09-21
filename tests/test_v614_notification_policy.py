from datetime import datetime, timezone
from src.notification_policy import NotificationPolicy, evaluate, validate_policy

def test_policy_defaults_and_payload():
    p = validate_policy("org-1", {})
    assert p.payload()["levels"] == ["DUE", "CRITICAL"]
    assert p.payload()["allow_external"] is True

def test_external_channels_require_explicit_opt_in():
    p = validate_policy("org-1", {})
    ok, reason = evaluate(p, level="CRITICAL", channel="EMAIL")
    assert ok
    p = validate_policy("org-1", {"allow_external": False})
    ok, reason = evaluate(p, level="CRITICAL", channel="EMAIL")
    assert not ok and "external" in reason

def test_level_and_channel_filters():
    p = validate_policy("org-1", {"levels": ["CRITICAL"], "channels": ["IN_APP"]})
    assert evaluate(p, level="DUE", channel="IN_APP")[0] is False
    assert evaluate(p, level="CRITICAL", channel="EMAIL")[0] is False
    assert evaluate(p, level="CRITICAL", channel="IN_APP")[0] is True

def test_quiet_window_blocks_notification():
    p = validate_policy("org-1", {"quiet_start": "22:00", "quiet_end": "07:00"})
    assert not evaluate(p, level="CRITICAL", channel="IN_APP", now=datetime(2026,1,1,23,0,tzinfo=timezone.utc))[0]
    assert evaluate(p, level="CRITICAL", channel="IN_APP", now=datetime(2026,1,1,12,0,tzinfo=timezone.utc))[0]

def test_invalid_policy_rejected():
    try: validate_policy("org-1", {"channels": ["SMS"]})
    except ValueError: pass
    else: assert False
