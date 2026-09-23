from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_v640_component_layer_exists_and_is_framework_free():
    js = (ROOT / "frontend/assets/ui-components.js").read_text(encoding="utf-8")
    assert "global.RDUI" in js
    for name in ["statusBadge", "kpiCard", "emptyState", "errorState", "loadingState", "evidenceCard", "timeline", "approvalGate"]:
        assert name in js
    assert "React" not in js
    assert "fetch(" not in js

def test_v640_component_layer_preserves_human_control_boundary():
    js = (ROOT / "frontend/assets/ui-components.js").read_text(encoding="utf-8")
    assert "Aucune action Google n’est exécutée automatiquement" in js
    assert "Approbation" in js
    assert "Action contrôlée" in js

def test_v640_component_blueprint_documents_data_and_permission_boundary():
    doc = (ROOT / "docs/COMPONENT_BLUEPRINT_V640.md").read_text(encoding="utf-8")
    assert "UI component → API client → server validation → authorization" in doc
    assert "Decision → Freeze → Human Approval → Controlled Preparation/Submission" in doc
    assert "ApprovalGate" in doc
