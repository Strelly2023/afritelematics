from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any


Match = tuple[str, str]


class FairnessEngine:
    """Canonical one-driver-to-one-rider allocation checks."""

    def allocate(
        self,
        drivers: Iterable[str],
        riders: Iterable[str],
    ) -> tuple[Match, ...]:
        drivers_sorted = tuple(sorted(str(driver) for driver in drivers))
        riders_sorted = tuple(sorted(str(rider) for rider in riders))
        return tuple(zip(drivers_sorted, riders_sorted))

    def validate_fairness(self, matches: Sequence[Match]) -> bool:
        seen_drivers: set[str] = set()
        seen_riders: set[str] = set()

        for driver, rider in matches:
            if driver in seen_drivers or rider in seen_riders:
                return False
            seen_drivers.add(driver)
            seen_riders.add(rider)

        return True

    def fairness_trace(self, matches: Sequence[Match]) -> dict[str, Any]:
        return {
            "matched_count": len(matches),
            "drivers": tuple(driver for driver, _ in matches),
            "riders": tuple(rider for _, rider in matches),
            "valid": self.validate_fairness(matches),
        }
