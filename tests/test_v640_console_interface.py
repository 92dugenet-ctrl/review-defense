from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v640_console_has_demo_mode_and_navigation_layer():
    js=(ROOT/'frontend/assets/app.js').read_text()
    css=(ROOT/'frontend/assets/app.css').read_text()
    assert "demoMode" in js
    assert "CASE-10482" in js
    assert "openCommandPalette" in js
    assert "workspace-switcher" in js
    assert "command-palette" in css
    assert "mobile-nav-toggle" in js

def test_v640_demo_keeps_server_action_boundary():
    js=(ROOT/'frontend/assets/app.js').read_text()
    assert "Aucune action externe ne sera exécutée" in js
    assert "googleapis.com" not in js
    assert "Idempotency-Key" in js

def test_v640_case_console_has_human_review_states():
    js=(ROOT/'frontend/assets/app.js').read_text()
    for value in ["IN_REVIEW","PENDING_APPROVAL","FROZEN","EVIDENCE_REQUIRED"]:
        assert value in js
    for fn in ["createDecision","freezeCase","approveCase","prepareSubmission"]:
        assert fn in js
