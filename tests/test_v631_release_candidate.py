from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rc_gate", ROOT / "scripts/release_candidate_gate.py")
rc = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(rc)


def test_contract_gate_passes():
    checks = rc.contract_checks()
    assert checks["all"] is True
    assert checks["version"] is True
    assert checks["security_headers"] is True
    assert checks["human_approval_gate"] is True
    assert checks["dr_source_is_explicit"] is True
    assert checks["dr_confirmation"] is True


def test_gate_never_accepts_skip_tests_as_release_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(rc, "contract_checks", lambda: {"all": True})
    monkeypatch.setattr(rc, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("tests must not run")))
    monkeypatch.setattr("sys.argv", ["release_candidate_gate.py", "--skip-tests", "--output", str(tmp_path / "report.json")])
    assert rc.main() == 1
    assert '"CONTRACT-PASS-NOT-RELEASE-GO"' in (tmp_path / "report.json").read_text()
