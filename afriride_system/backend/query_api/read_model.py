"""Read model facade for Phase 1 app state."""

from __future__ import annotations

from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRideCommandDispatcher,
)


class AfriRideReadModel:
    def __init__(self, dispatcher: AfriRideCommandDispatcher) -> None:
        self.dispatcher = dispatcher

    def ride(self, ride_id: str) -> dict:
        return self.dispatcher.ride_status(ride_id)

    def driver_requests(self, driver_id: str) -> list[dict]:
        return self.dispatcher.driver_requests(driver_id)
