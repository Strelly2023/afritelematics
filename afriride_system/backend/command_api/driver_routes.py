"""Driver command routes as adapter-only callables."""

from __future__ import annotations

from typing import Any

from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRideCommandDispatcher,
)


class DriverRoutes:
    def __init__(self, dispatcher: AfriRideCommandDispatcher) -> None:
        self.dispatcher = dispatcher

    def status(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.dispatcher.set_driver_status(
            driver_id=payload["driver_id"],
            online=payload["online"],
        )

    def requests(self, driver_id: str) -> list[dict[str, Any]]:
        return self.dispatcher.driver_requests(driver_id)

    def accept(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.dispatcher.accept_ride(
            driver_id=payload["driver_id"],
            ride_id=payload["ride_id"],
        )

    def start(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.dispatcher.start_trip(
            driver_id=payload["driver_id"],
            ride_id=payload["ride_id"],
        )

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.dispatcher.complete_trip(
            driver_id=payload["driver_id"],
            ride_id=payload["ride_id"],
        )
