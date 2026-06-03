"""Canonical AfriRide ride model.

This module defines ride data only. It intentionally does not perform matching,
routing, pricing, persistence, or state transitions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Mapping

from ecosystems.afriride.domain.state.ride_state import RideStatus


class RideModelViolation(ValueError):
    """Raised when a ride declaration is incomplete or invalid."""


@dataclass(frozen=True)
class Ride:
    """Declared ride execution unit for AfriRide."""

    id: str
    passenger_id: str
    pickup_location: Mapping[str, Any]
    dropoff_location: Mapping[str, Any]
    requested_at: str
    assigned_driver: str | None = None
    route_plan: Mapping[str, Any] | None = None
    price_plan: Mapping[str, Any] | None = None
    status: RideStatus | str = field(default=RideStatus.REQUESTED)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_text("id", self.id))
        object.__setattr__(
            self,
            "passenger_id",
            _require_text("passenger_id", self.passenger_id),
        )
        object.__setattr__(
            self,
            "requested_at",
            _require_text("requested_at", self.requested_at),
        )
        object.__setattr__(
            self,
            "pickup_location",
            _require_mapping("pickup_location", self.pickup_location),
        )
        object.__setattr__(
            self,
            "dropoff_location",
            _require_mapping("dropoff_location", self.dropoff_location),
        )
        object.__setattr__(
            self,
            "assigned_driver",
            _optional_text("assigned_driver", self.assigned_driver),
        )
        object.__setattr__(
            self,
            "route_plan",
            _optional_mapping("route_plan", self.route_plan),
        )
        object.__setattr__(
            self,
            "price_plan",
            _optional_mapping("price_plan", self.price_plan),
        )
        object.__setattr__(self, "status", _normalize_status(self.status))

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready representation."""

        return {
            "assigned_driver": self.assigned_driver,
            "dropoff_location": _canonicalize(self.dropoff_location),
            "id": self.id,
            "passenger_id": self.passenger_id,
            "pickup_location": _canonicalize(self.pickup_location),
            "price_plan": _canonicalize(self.price_plan),
            "requested_at": self.requested_at,
            "route_plan": _canonicalize(self.route_plan),
            "status": self.status.value,
        }

    def canonical_json(self) -> str:
        """Return stable canonical JSON for trace and replay inputs."""

        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def ride_hash(self) -> str:
        """Return a deterministic content hash of the declared ride."""

        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _require_text(field_name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RideModelViolation(f"{field_name} must be declared as non-empty text")
    return value


def _optional_text(field_name: str, value: str | None) -> str | None:
    if value is None:
        return None
    return _require_text(field_name, value)


def _require_mapping(field_name: str, value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not value:
        raise RideModelViolation(f"{field_name} must be declared as a non-empty mapping")
    return _canonicalize(value)


def _optional_mapping(
    field_name: str,
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    return _require_mapping(field_name, value)


def _normalize_status(value: RideStatus | str) -> RideStatus:
    if isinstance(value, RideStatus):
        return value
    try:
        return RideStatus(value)
    except ValueError as exc:
        raise RideModelViolation(f"status must be a valid RideStatus: {value}") from exc


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value
