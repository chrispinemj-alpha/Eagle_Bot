import pytest
from eagle_bot.core.coworkers import CoworkerRegistry
from eagle_bot.core.governance import ActionRequest, Governance, RiskLevel
from eagle_bot.core.identity import Identity
from eagle_bot.core.kill_switch import KillSwitch
from eagle_bot.core.orders import WorkOrder
from eagle_bot.core.orchestration import Orchestrator


def test_identity_validation():
    Identity(display_name="Whizz").validate()
    with pytest.raises(ValueError):
        Identity(display_name="").validate()


def test_coworker_registry():
    registry = CoworkerRegistry()
    assert {c.key for c in registry.list()} >= {"generalist", "researcher", "builder", "analyst", "operator", "educator"}


def test_orchestration_prepares_order_without_executing_it():
    order = WorkOrder(owner_id="u1", objective="Understand a problem")
    result = Orchestrator().prepare(order)
    assert result["status"] == "prepared"
    assert order.status == "queued"


def test_governance_requires_approval_for_high_risk():
    request = ActionRequest("send_payment", RiskLevel.HIGH, "u1")
    governance = Governance()
    assert governance.requires_approval(request)
    assert not governance.can_execute(request)
    assert governance.can_execute(request, approved=True)


def test_critical_action_is_not_implicitly_allowed():
    request = ActionRequest("critical_action", RiskLevel.CRITICAL, "u1")
    assert not Governance().can_execute(request)


def test_kill_switch_blocks_execution():
    switch = KillSwitch()
    switch.engage()
    with pytest.raises(RuntimeError):
        switch.assert_execution_allowed()


def test_unknown_coworker_rejected():
    with pytest.raises(KeyError):
        Orchestrator().prepare(WorkOrder("u1", "x", "does-not-exist"))
