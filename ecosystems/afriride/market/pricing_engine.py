from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class PricingEngine:
    """Pure deterministic pricing with a hard multiplier cap."""

    def __init__(self, *, max_multiplier: Decimal | str = "3.0") -> None:
        self.max_multiplier = Decimal(str(max_multiplier))
        if self.max_multiplier < Decimal("1.0"):
            raise ValueError("max_multiplier must be at least 1.0")

    def calculate_price(
        self,
        base_price: Decimal | int | str,
        demand: int,
        supply: int,
    ) -> Decimal:
        if demand < 0:
            raise ValueError("demand must be non-negative")
        if supply < 0:
            raise ValueError("supply must be non-negative")

        base = Decimal(str(base_price))
        if base < Decimal("0"):
            raise ValueError("base_price must be non-negative")

        multiplier = self.price_multiplier(demand=demand, supply=supply)
        return (base * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def price_multiplier(self, *, demand: int, supply: int) -> Decimal:
        if supply == 0:
            return self.max_multiplier
        ratio = Decimal(demand) / Decimal(supply)
        return min(max(Decimal("1.0"), ratio), self.max_multiplier)
