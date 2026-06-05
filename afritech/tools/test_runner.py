from __future__ import annotations

import asyncio
from typing import Dict

from afritech.distributed.testing.adversarial_attack_suite import (
    run_adversarial_attack_simulation_suite,
)
from afritech.distributed.testing.hardening_suite import (
    run_system_integration_hardening_suite,
)
from afritech.distributed.testing.protocol_scenarios import (
    run_multi_scenario_protocol_validation,
)
from afritech.distributed.testing.twenty_node_adversarial_network import (
    simulate_twenty_node_adversarial_network,
)


def run_all_tests() -> Dict[str, object]:
    hardening = asyncio.run(run_system_integration_hardening_suite())
    attacks = run_adversarial_attack_simulation_suite()
    scenarios = run_multi_scenario_protocol_validation()
    scale = simulate_twenty_node_adversarial_network()
    passed = (
        hardening["passed"]
        and attacks["passed"]
        and scenarios["passed"]
        and scale["passed"]
    )
    return {
        "passed": passed,
        "hardening": hardening,
        "adversarial": attacks,
        "scenarios": scenarios,
        "scale": scale,
    }
