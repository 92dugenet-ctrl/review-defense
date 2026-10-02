from src.policy_workspace import (
    policy_catalog, build_policy_workspace, get_policy, create_policy_version,
    can_edit_policy, can_validate_policy, can_publish_policy, can_modify_policy,
)

def test_policy_catalog_contains_all_ten_policies():
    policies = policy_catalog()
    assert len(policies) == 10
    assert [p.code for p in policies] == [f"RD-P{i:02d}" for i in range(1, 11)]


def test_every_policy_has_signal_and_counter_signal():
    for policy in policy_catalog():
        kinds = {s.kind for s in policy.signals}
        assert "SIGNAL" in kinds
        assert "COUNTER_SIGNAL" in kinds
        assert all(s.evidence_required for s in policy.signals)


def test_policy_workspace_is_tenant_bound():
    ws = build_policy_workspace("org-a")
    assert ws.organization_id == "org-a"
    assert len(ws.policies) == 10


def test_unknown_policy_is_rejected():
    try:
        get_policy("RD-P99")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown policy should fail")


def test_policy_version_requires_human_validation():
    draft = create_policy_version("RD-P10", "1.1", "2026-09-20T12:00:00Z")
    assert draft.validation_status == "PENDING"
    assert draft.validated_by is None
    validated = create_policy_version("RD-P10", "1.1", "2026-09-20T12:00:00Z", validated_by="u-admin")
    assert validated.validation_status == "VALIDATED"
    assert validated.validated_by == "u-admin"


def test_policy_permissions():
    assert can_edit_policy("ANALYST")
    assert can_validate_policy("ADMIN")
    assert can_publish_policy("OWNER")
    assert not can_validate_policy("ANALYST")
    assert not can_publish_policy("CLIENT")
    assert can_modify_policy("ANALYST", "EDIT")
    assert not can_modify_policy("ANALYST", "VALIDATE")
