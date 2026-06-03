from __future__ import annotations

from decimal import Decimal


class SurgeModel:
    """Bounded deterministic surge model; seed is recorded, not random authority."""

    def compute_surge(self, demand: int, supply: int, seed: int) -> Decimal:
        if demand < 0:
            raise ValueError("demand must be non-negative")
        if supply < 0:
            raise ValueError("supply must be non-negative")
        int(seed)

        if supply == 0:
            return Decimal("3.0")

        ratio = Decimal(demand) / Decimal(max(supply, 1))
        if ratio < Decimal("1.0"):
            return Decimal("1.0")
        if ratio < Decimal("2.0"):
            return Decimal("1.5")
        return Decimal("2.5")
