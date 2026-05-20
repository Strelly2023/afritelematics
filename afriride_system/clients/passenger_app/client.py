"""Minimal passenger app client for Phase 1 simulation."""

from __future__ import annotations

from afriride_system.backend.command_api.passenger_routes import PassengerRoutes


class PassengerApp:
    def __init__(self, passenger_id: str, routes: PassengerRoutes) -> None:
        self.passenger_id = passenger_id
        self.routes = routes

    def request_ride(
        self,
        *,
        pickup: str,
        destination: str,
        ride_id: str | None = None,
    ) -> dict:
        return self.routes.request_ride(
            {
                "passenger_id": self.passenger_id,
                "pickup": pickup,
                "destination": destination,
                "ride_id": ride_id,
            }
        )

    def status(self, ride_id: str) -> dict:
        return self.routes.status(ride_id)

    def cancel(self, ride_id: str) -> dict:
        return self.routes.cancel(
            {
                "passenger_id": self.passenger_id,
                "ride_id": ride_id,
            }
        )
