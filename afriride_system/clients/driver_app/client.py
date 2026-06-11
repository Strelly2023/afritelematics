"""Minimal driver app client for Phase 1 simulation."""

from __future__ import annotations

from afriride_system.backend.command_api.driver_routes import DriverRoutes


class DriverApp:
    def __init__(self, driver_id: str, routes: DriverRoutes) -> None:
        self.driver_id = driver_id
        self.routes = routes

    def go_online(self) -> dict:
        return self.routes.status(
            {
                "driver_id": self.driver_id,
                "online": True,
            }
        )

    def go_offline(self) -> dict:
        return self.routes.status(
            {
                "driver_id": self.driver_id,
                "online": False,
            }
        )

    def requests(self) -> list[dict]:
        return self.routes.requests(self.driver_id)

    def accept(self, ride_id: str) -> dict:
        return self.routes.accept(
            {
                "driver_id": self.driver_id,
                "ride_id": ride_id,
            }
        )

    def start(self, ride_id: str) -> dict:
        return self.routes.start(
            {
                "driver_id": self.driver_id,
                "ride_id": ride_id,
            }
        )

    def arrive(self, ride_id: str) -> dict:
        return self.routes.arrive(
            {
                "driver_id": self.driver_id,
                "ride_id": ride_id,
            }
        )

    def complete(self, ride_id: str) -> dict:
        return self.routes.complete(
            {
                "driver_id": self.driver_id,
                "ride_id": ride_id,
            }
        )
