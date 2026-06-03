from __future__ import annotations

from ecosystems.afriride.market.fairness_engine import FairnessEngine
from ecosystems.afriride.market.market_simulator import MarketSimulator
from ecosystems.afriride.market.pricing_engine import PricingEngine
from ecosystems.afriride.market.surge_model import SurgeModel


def test_fair_allocation() -> None:
    engine = FairnessEngine()

    drivers = ["d2", "d1"]
    riders = ["r2", "r1"]

    matches = engine.allocate(drivers, riders)

    assert matches == (("d1", "r1"), ("d2", "r2"))
    assert engine.validate_fairness(matches)


def test_duplicate_allocation_is_rejected_by_fairness_check() -> None:
    engine = FairnessEngine()

    assert not engine.validate_fairness((("d1", "r1"), ("d1", "r2")))
    assert not engine.validate_fairness((("d1", "r1"), ("d2", "r1")))


def test_market_simulator_is_replay_stable() -> None:
    simulator = MarketSimulator(PricingEngine(), SurgeModel(), FairnessEngine())
    drivers = ["d3", "d1", "d2"]
    riders = ["r2", "r3", "r1"]

    first = simulator.run(10, 9, 3, drivers, riders)
    second = simulator.run(10, 9, 3, list(reversed(drivers)), list(reversed(riders)))

    assert first == second
    assert first["fairness"]["valid"] is True
    assert first["market_trace"]["stages"] == ["pricing", "surge", "fairness"]
