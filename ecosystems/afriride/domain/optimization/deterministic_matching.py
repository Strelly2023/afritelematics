"""Deterministic AfriRide driver matching.

Matching is the first bounded optimization layer. It returns a declared
assignment candidate only; it does not mutate rides, emit events, calculate
routes, or advance lifecycle state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from math import sqrt
from typing import Any, Mapping, Sequence

from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.state.ride_lifecycle_dag import (
    RideLifecycleState,
    assert_transition,
)


class MatchingViolation(ValueError):
    """Raised when matching inputs are undeclared or invalid."""


@dataclass(frozen=True)
class DriverAssignment:
    """Deterministic matching output for a ride."""

    ride_id: str
    ride_hash: str
    driver_id: str
    ride_partition: str
    driver_partition: str
    distance: float
    locality: str
    score: tuple[int, float, str]

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready assignment representation."""

        return {
            "distance": self.distance,
            "driver_id": self.driver_id,
            "driver_partition": self.driver_partition,
            "locality": self.locality,
            "ride_hash": self.ride_hash,
            "ride_id": self.ride_id,
            "ride_partition": self.ride_partition,
            "score": list(self.score),
        }

    def canonical_json(self) -> str:
        """Return stable canonical JSON for trace and replay."""

        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def assignment_hash(self) -> str:
        """Return a deterministic content hash for the assignment."""

        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


def match_driver(
    ride: Ride,
    drivers: Sequence[Mapping[str, Any]],
    *,
    allow_cross_partition: bool = False,
) -> DriverAssignment | None:
    """Return the deterministic best driver assignment for a ride."""

    assert_transition(RideLifecycleState.REQUESTED, RideLifecycleState.MATCHED)
    if not isinstance(ride, Ride):
        raise MatchingViolation("ride must be a canonical Ride")

    ride_partition = _extract_partition("ride.pickup_location", ride.pickup_location)
    pickup = _extract_point("ride.pickup_location", ride.pickup_location)
    candidates = [
        _candidate_score(driver, pickup, ride_partition, allow_cross_partition)
        for driver in drivers
    ]
    candidates = [candidate for candidate in candidates if candidate is not None]

    if not candidates:
        return None

    ordered = sorted(
        candidates,
        key=lambda candidate: candidate["score"],
    )
    selected = ordered[0]

    return DriverAssignment(
        ride_id=ride.id,
        ride_hash=ride.ride_hash(),
        driver_id=selected["driver_id"],
        ride_partition=ride_partition,
        driver_partition=selected["driver_partition"],
        distance=selected["distance"],
        locality=selected["locality"],
        score=selected["score"],
    )


def rank_driver_candidates(
    ride: Ride,
    drivers: Sequence[Mapping[str, Any]],
    *,
    allow_cross_partition: bool = False,
) -> tuple[DriverAssignment, ...]:
    """Return all admissible candidates in deterministic match order."""

    assignment = match_driver(
        ride,
        drivers,
        allow_cross_partition=allow_cross_partition,
    )
    if assignment is None:
        return ()

    ride_partition = _extract_partition("ride.pickup_location", ride.pickup_location)
    pickup = _extract_point("ride.pickup_location", ride.pickup_location)
    candidates = [
        _candidate_score(driver, pickup, ride_partition, allow_cross_partition)
        for driver in drivers
    ]
    ranked = sorted(
        (candidate for candidate in candidates if candidate is not None),
        key=lambda candidate: candidate["score"],
    )
    return tuple(
        DriverAssignment(
            ride_id=ride.id,
            ride_hash=ride.ride_hash(),
            driver_id=candidate["driver_id"],
            ride_partition=ride_partition,
            driver_partition=candidate["driver_partition"],
            distance=candidate["distance"],
            locality=candidate["locality"],
            score=candidate["score"],
        )
        for candidate in ranked
    )


def _candidate_score(
    driver: Mapping[str, Any],
    pickup: Mapping[str, float],
    ride_partition: str,
    allow_cross_partition: bool,
) -> dict[str, Any] | None:
    if not isinstance(driver, Mapping):
        raise MatchingViolation("driver candidate must be a declared mapping")

    driver_id = _require_text("driver.id", driver.get("id"))
    driver_partition = _extract_partition(f"driver.{driver_id}", driver)
    if driver_partition != ride_partition and not allow_cross_partition:
        return None

    driver_point = _extract_point(f"driver.{driver_id}", driver)
    distance = _distance(driver_point, pickup)
    locality_rank = 0 if driver_partition == ride_partition else 1
    locality = "same_partition" if locality_rank == 0 else "declared_cross_partition"
    return {
        "distance": distance,
        "driver_id": driver_id,
        "driver_partition": driver_partition,
        "locality": locality,
        "score": (locality_rank, distance, driver_id),
    }


def _extract_partition(field_name: str, value: Mapping[str, Any]) -> str:
    return _require_text(f"{field_name}.zone", value.get("zone"))


def _extract_point(field_name: str, value: Mapping[str, Any]) -> dict[str, float]:
    return {
        "lat": _require_number(f"{field_name}.lat", value.get("lat")),
        "lng": _require_number(f"{field_name}.lng", value.get("lng")),
    }


def _distance(first: Mapping[str, float], second: Mapping[str, float]) -> float:
    return round(
        sqrt((first["lat"] - second["lat"]) ** 2 + (first["lng"] - second["lng"]) ** 2),
        9,
    )


def _require_text(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MatchingViolation(f"{field_name} must be declared as non-empty text")
    return value


def _require_number(field_name: str, value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise MatchingViolation(f"{field_name} must be declared as a number")
    return float(value)
