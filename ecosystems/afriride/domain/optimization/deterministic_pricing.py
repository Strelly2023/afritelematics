"""Deterministic AfriRide price calculation.

Pricing is a bounded optimization artifact. It consumes declared ride,
assignment, route, and pricing configuration inputs, then returns an immutable
price plan without mutating execution state or consulting live demand signals.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from typing import Any

from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_matching import (
    DriverAssignment,
)
from ecosystems.afriride.domain.optimization.deterministic_routing import RoutePlan


class PricingViolation(ValueError):
    """Raised when pricing inputs are undeclared or inconsistent."""


@dataclass(frozen=True)
class PricingConfig:
    """Declared pricing policy for deterministic fare calculation."""

    base_fare: Decimal | int | float | str
    per_distance_rate: Decimal | int | float | str
    per_time_rate: Decimal | int | float | str
    currency: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_fare", _money("base_fare", self.base_fare))
        object.__setattr__(
            self,
            "per_distance_rate",
            _money("per_distance_rate", self.per_distance_rate),
        )
        object.__setattr__(
            self,
            "per_time_rate",
            _money("per_time_rate", self.per_time_rate),
        )
        object.__setattr__(self, "currency", _require_text("currency", self.currency))

    def to_canonical_dict(self) -> dict[str, str]:
        """Return deterministic JSON-ready pricing config."""

        return {
            "base_fare": _decimal_text(self.base_fare),
            "currency": self.currency,
            "per_distance_rate": _decimal_text(self.per_distance_rate),
            "per_time_rate": _decimal_text(self.per_time_rate),
        }

    def config_hash(self) -> str:
        """Return a deterministic content hash for this pricing policy."""

        return sha256(
            json.dumps(
                self.to_canonical_dict(),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class PricePlan:
    """Deterministic pricing output for a ride."""

    ride_id: str
    ride_hash: str
    assignment_hash: str
    route_hash: str
    pricing_config_hash: str
    base_fare: Decimal
    distance_cost: Decimal
    time_cost: Decimal
    total_cost: Decimal
    currency: str

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-ready price representation."""

        return {
            "assignment_hash": self.assignment_hash,
            "base_fare": _decimal_text(self.base_fare),
            "currency": self.currency,
            "distance_cost": _decimal_text(self.distance_cost),
            "price_basis": "base_plus_distance_plus_time",
            "pricing_config_hash": self.pricing_config_hash,
            "ride_hash": self.ride_hash,
            "ride_id": self.ride_id,
            "route_hash": self.route_hash,
            "time_cost": _decimal_text(self.time_cost),
            "total_cost": _decimal_text(self.total_cost),
        }

    def canonical_json(self) -> str:
        """Return stable canonical JSON for trace and replay."""

        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def price_hash(self) -> str:
        """Return a deterministic content hash for the price plan."""

        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


def compute_price(
    ride: Ride,
    assignment: DriverAssignment,
    route: RoutePlan,
    pricing_config: PricingConfig,
) -> PricePlan:
    """Compute a deterministic price plan from declared artifacts."""

    if not isinstance(ride, Ride):
        raise PricingViolation("ride must be a canonical Ride")
    if not isinstance(assignment, DriverAssignment):
        raise PricingViolation("assignment must be a DriverAssignment")
    if not isinstance(route, RoutePlan):
        raise PricingViolation("route must be a RoutePlan")
    if not isinstance(pricing_config, PricingConfig):
        raise PricingViolation("pricing_config must be a PricingConfig")

    ride_hash = ride.ride_hash()
    if assignment.ride_id != ride.id or assignment.ride_hash != ride_hash:
        raise PricingViolation("assignment does not match ride")
    if route.ride_id != ride.id or route.ride_hash != ride_hash:
        raise PricingViolation("route does not match ride")

    distance_cost = _money(
        "distance_cost",
        Decimal(str(route.distance)) * pricing_config.per_distance_rate,
    )
    time_cost = _money(
        "time_cost",
        Decimal(str(route.estimated_time)) * pricing_config.per_time_rate,
    )
    total_cost = _money(
        "total_cost",
        pricing_config.base_fare + distance_cost + time_cost,
    )

    return PricePlan(
        ride_id=ride.id,
        ride_hash=ride_hash,
        assignment_hash=assignment.assignment_hash(),
        route_hash=route.route_hash(),
        pricing_config_hash=pricing_config.config_hash(),
        base_fare=pricing_config.base_fare,
        distance_cost=distance_cost,
        time_cost=time_cost,
        total_cost=total_cost,
        currency=pricing_config.currency,
    )


def _money(field_name: str, value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, bool):
        raise PricingViolation(f"{field_name} must be declared as a non-negative number")
    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise PricingViolation(
            f"{field_name} must be declared as a non-negative number"
        ) from exc
    if amount < 0:
        raise PricingViolation(f"{field_name} must be declared as a non-negative number")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_text(value: Decimal) -> str:
    return format(value, ".2f")


def _require_text(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PricingViolation(f"{field_name} must be declared as non-empty text")
    return value
