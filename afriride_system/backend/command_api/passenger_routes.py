"""Passenger command routes as adapter-only callables."""

from __future__ import annotations

from typing import Any

from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRideCommandDispatcher,
)


class PassengerRoutes:
    def __init__(self, dispatcher: AfriRideCommandDispatcher) -> None:
        self.dispatcher = dispatcher

    def request_ride(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.dispatcher.request_ride(
            passenger_id=payload["passenger_id"],
            pickup=payload["pickup"],
            destination=payload["destination"],
            ride_id=payload.get("ride_id"),
        )

    def status(self, ride_id: str) -> dict[str, Any]:
        return self.dispatcher.ride_status(ride_id)

    def cancel(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.dispatcher.cancel_ride(
            passenger_id=payload["passenger_id"],
            ride_id=payload["ride_id"],
        )
