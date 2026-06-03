from __future__ import annotations

from decimal import Decimal

from ecosystems.afriride.market.surge_model import SurgeModel


def test_surge_deterministic() -> None:
    model = SurgeModel()

    s1 = model.compute_surge(10, 5, seed=42)
    s2 = model.compute_surge(10, 5, seed=42)

    assert s1 == s2
    assert s1 == Decimal("2.5")


def test_surge_is_bounded_under_zero_supply() -> None:
    model = SurgeModel()

    assert model.compute_surge(100, 0, seed=42) == Decimal("3.0")
