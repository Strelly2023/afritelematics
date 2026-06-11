"""Interface-layer state models for AfriRide Phase 1."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class DriverSession:
    driver_id: str
    online: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "driver_id": self.driver_id,
            "online": self.online,
        }

    @classmethod
    def from_snapshot(cls, payload: dict[str, Any]) -> "DriverSession":
        return cls(
            driver_id=str(payload["driver_id"]),
            online=bool(payload.get("online", False)),
        )


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

    @classmethod
    def from_snapshot(cls, payload: dict[str, Any]) -> "RideSession":
        return cls(
            ride_id=str(payload["ride_id"]),
            passenger_id=str(payload["passenger_id"]),
            pickup=str(payload["pickup"]),
            destination=str(payload["destination"]),
            status=str(payload.get("status", "REQUESTED")),
            assigned_driver=payload.get("assigned_driver"),
            trace_hash=payload.get("trace_hash"),
            state_hash=payload.get("state_hash"),
            events=tuple(str(event) for event in payload.get("events", ())),
        )
