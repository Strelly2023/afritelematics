from __future__ import annotations

from afritech.distributed.services.state_service import StateService
from afritech.distributed.testing.afriride_ledger_scenario import (
    run_afriride_ledger_scenario,
)
from afritech.distributed.testing.pilot_activation_checklist import (
    REQUIRED_LIVE_GATES,
    build_pilot_activation_checklist,
)
from afritech.distributed.testing.protocol_scenarios import run_finance_scenario
from afritech.distributed.testing.twenty_node_adversarial_network import (
    simulate_twenty_node_adversarial_network,
)


def test_pilot_activation_checklist_defaults_to_hold():
    checklist = build_pilot_activation_checklist()

    assert checklist["authorized"] is False
    assert checklist["classification"] == "activation_prepared_hold"
    assert set(checklist["live_gates"]) == set(REQUIRED_LIVE_GATES)


def test_pilot_activation_checklist_authorizes_only_when_all_gates_true():
    checklist = build_pilot_activation_checklist(
        {gate: True for gate in REQUIRED_LIVE_GATES}
    )

    assert checklist["authorized"] is True
    assert checklist["classification"] == "go_authorized"


def test_twenty_node_adversarial_network_rejects_bad_minority():
    report = simulate_twenty_node_adversarial_network()

    assert report["passed"] is True
    assert report["node_count"] == 20
    assert len(report["adversarial_nodes"]) == 4
    assert len(report["accepted_nodes"]) == 16
    assert report["chain_valid"] is True


def test_state_service_queries_afriride_state():
    scenario = run_afriride_ledger_scenario()
    service = StateService()
    service.load_state(scenario["state"])

    ride = service.get_ride("ride-001")
    receipt = service.get_receipt("receipt-ride-001")

    assert ride is not None
    assert ride["status"] == "completed"
    assert receipt is not None
    assert receipt["fare"] > 0


def test_state_service_queries_finance_state():
    scenario = run_finance_scenario()
    service = StateService()
    service.load_state(scenario["state"])

    assert service.get_account_balance("acct-a") == 75
    assert service.get_account_balance("acct-b") == 35
