"""Interface-layer state models for AfriRide Phase 1."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class DriverSession:
    driver_id: str
    online: bool = False


@dataclass(frozen=True)
class RideSession:
    ride_id: str
    passenger_id: str
    pickup: str
    destination: str
    status: str = "REQUESTED"
    assigned_driver: str | None = None
    trace_hash: str | None = None
    state_hash: str | None = None
    events: tuple[str, ...] = field(default_factory=tuple)

    def with_update(self, **changes: Any) -> "RideSession":
        return replace(self, **changes)

    def snapshot(self) -> dict[str, Any]:
        return {
            "ride_id": self.ride_id,
            "passenger_id": self.passenger_id,
            "pickup": self.pickup,
            "destination": self.destination,
            "status": self.status,
            "assigned_driver": self.assigned_driver,
            "trace_hash": self.trace_hash,
            "state_hash": self.state_hash,
            "events": list(self.events),
        }
