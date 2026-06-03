from __future__ import annotations

from decimal import Decimal
from typing import Any

from afritech.simulation.validation_receipt import stable_hash
from ecosystems.afriride.market.fairness_engine import FairnessEngine
from ecosystems.afriride.market.pricing_engine import PricingEngine
from ecosystems.afriride.market.surge_model import SurgeModel


class MarketSimulator:
    """Replay-stable pricing, surge, and fairness simulation."""

    def __init__(
        self,
        pricing: PricingEngine,
        surge: SurgeModel,
        fairness: FairnessEngine,
    ) -> None:
        self.pricing = pricing
        self.surge = surge
        self.fairness = fairness

    def run(
        self,
        base_price: Decimal | int | str,
        demand: int,
        supply: int,
        drivers: tuple[str, ...] | list[str],
        riders: tuple[str, ...] | list[str],
        *,
        seed: int = 42,
    ) -> dict[str, Any]:
        surge_multiplier = self.surge.compute_surge(demand, supply, seed=seed)
        price = self.pricing.calculate_price(base_price, demand, supply)
        matches = self.fairness.allocate(drivers, riders)
        fairness_trace = self.fairness.fairness_trace(matches)

        state = {
            "base_price": str(Decimal(str(base_price))),
            "demand": demand,
            "supply": supply,
            "price": str(price),
            "surge": str(surge_multiplier),
            "matches": tuple({"driver": driver, "rider": rider} for driver, rider in matches),
            "fairness": fairness_trace,
            "market_trace": {
                "stages": ["pricing", "surge", "fairness"],
                "pricing_rule": "bounded_demand_supply_ratio",
                "allocation_rule": "canonical_one_to_one",
            },
        }
        state["market_hash"] = stable_hash(state)
        return state
