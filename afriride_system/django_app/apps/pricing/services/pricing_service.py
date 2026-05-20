"""Deterministic pricing skeleton."""

from __future__ import annotations


class PricingService:
    BASE_FARE = 5.0
    PER_KM = 1.5

    @staticmethod
    def calculate(distance_km: float) -> float:
        if distance_km < 0:
            raise ValueError("distance_km must be non-negative")
        return round(PricingService.BASE_FARE + (distance_km * PricingService.PER_KM), 2)
