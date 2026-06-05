from __future__ import annotations

import asyncio

from afritech.distributed.testing.adversarial_attack_suite import (
    run_adversarial_attack_simulation_suite,
)
from afritech.distributed.testing.hardening_suite import (
    run_system_integration_hardening_suite,
)
from afritech.distributed.testing.production_pilot_prep import (
    build_afriride_multi_node_pilot_readiness,
)
from afritech.distributed.testing.protocol_scenarios import (
    run_multi_scenario_protocol_validation,
)


def test_system_integration_hardening_suite_passes():
    report = asyncio.run(run_system_integration_hardening_suite())

    assert report["passed"] is True
    assert {s["scenario"] for s in report["scenarios"]} == {
        "async_execution_stress",
        "network_instability",
        "partial_node_failure",
    }


def test_multi_scenario_protocol_validation_passes():
    report = run_multi_scenario_protocol_validation()

    assert report["passed"] is True
    scenarios = {scenario["scenario"]: scenario for scenario in report["scenarios"]}
    assert scenarios["logistics"]["state"]["shipments"]["ship-001"]["status"] == "delivered"
    assert scenarios["finance"]["state"]["balances"]["acct-a"] == 75
    assert scenarios["supply_chain"]["state"]["lots"]["lot-001"]["status"] == "released"


def test_adversarial_attack_simulation_suite_passes():
    report = run_adversarial_attack_simulation_suite()

    assert report["passed"] is True
    assert len(report["attacks"]) == 5
    assert all(attack["detected"] for attack in report["attacks"])


def test_afriride_multi_node_pilot_readiness_prepares_but_holds_live_go():
    report = asyncio.run(build_afriride_multi_node_pilot_readiness())

    assert report["repo_side_ready"] is True
    assert report["go_authorized"] is False
    assert report["classification"] == "pilot_prepared_live_execution_hold"
