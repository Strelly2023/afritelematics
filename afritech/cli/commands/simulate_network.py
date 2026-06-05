from __future__ import annotations

from typing import Dict

from afritech.distributed.testing.twenty_node_adversarial_network import (
    simulate_twenty_node_adversarial_network,
)
from afritech.distributed.testing.sovereign_ledger_protocol import (
    run_five_node_validation,
)


def run() -> Dict[str, object]:
    return run_twenty_node()


def run_twenty_node() -> Dict[str, object]:
    report = simulate_twenty_node_adversarial_network()
    return {
        "command": "simulate-20-node",
        "status": "passed" if report["passed"] else "failed",
        "summary": (
            f"20-node adversarial simulation: "
            f"{'PASS' if report['passed'] else 'FAIL'}"
        ),
        "report": report,
    }


def run_five_node() -> Dict[str, object]:
    report = run_five_node_validation()
    passed = report["chain_valid"] and report["consensus"]["votes"] == 5
    return {
        "command": "simulate-5-node",
        "status": "passed" if passed else "failed",
        "summary": f"5-node consensus simulation: {'PASS' if passed else 'FAIL'}",
        "report": report,
    }
