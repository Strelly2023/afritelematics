from __future__ import annotations

import sys
from decimal import Decimal
from typing import Any

from afritech.simulation.validation_receipt import build_validation_receipt
from ecosystems.afriride.market.fairness_engine import FairnessEngine
from ecosystems.afriride.market.market_simulator import MarketSimulator
from ecosystems.afriride.market.pricing_engine import PricingEngine
from ecosystems.afriride.market.surge_model import SurgeModel

#afritech.ci.fairness_validator

def validate_market(trace: tuple[dict[str, Any], ...]) -> None:
    for state in trace:
        if Decimal(str(state["price"])) < Decimal("0"):
            raise AssertionError("negative market price")
        if Decimal(str(state["surge"])) < Decimal("1.0"):
            raise AssertionError("surge below neutral multiplier")
        if Decimal(str(state["surge"])) > Decimal("3.0"):
            raise AssertionError("surge cap exceeded")
        if state["fairness"]["valid"] is not True:
            raise AssertionError("fairness invariant failed")


def build_receipt():
    simulator = MarketSimulator(PricingEngine(), SurgeModel(), FairnessEngine())
    scenarios = (
        simulator.run(10, 10, 5, ["d2", "d1"], ["r2", "r1"]),
        simulator.run(10, 100, 0, ["d1"], ["r1", "r2"]),
        simulator.run("12.50", 8, 4, ["d3", "d1", "d2"], ["r2", "r3", "r1"]),
    )
    replayed = (
        simulator.run(10, 10, 5, ["d1", "d2"], ["r1", "r2"]),
        simulator.run(10, 100, 0, ["d1"], ["r2", "r1"]),
        simulator.run("12.50", 8, 4, ["d2", "d3", "d1"], ["r1", "r2", "r3"]),
    )

    if scenarios != replayed:
        raise RuntimeError("Market replay divergence detected")
    validate_market(scenarios)

    return build_validation_receipt(
        surface="ecosystems.afriride.market.market_simulator",
        validator="afritech.ci.fairness_validator",
        inputs={
            "scenario_count": len(scenarios),
            "rules": ("bounded_pricing", "bounded_surge", "canonical_one_to_one"),
        },
        outputs={
            "market_hashes": tuple(state["market_hash"] for state in scenarios),
            "max_price": max(state["price"] for state in scenarios),
        },
        trace=scenarios,
        evidence=(
            "pricing_replay_equivalence",
            "surge_stability_trace",
            "fairness_trace_validation",
            "market_imbalance_trace",
            "exploitation_resistance_trace",
        ),
    )


def run() -> None:
    receipt = build_receipt()
    if not receipt.deterministic or not receipt.replay_safe:
        raise RuntimeError("Fairness validation receipt is not replay safe")
    print("Fairness validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Fairness validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
