"""Adapter from app commands to the existing AfriRide deterministic executor."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from uuid import uuid4

from ecosystems.afriride.continuity.resolution import canonical_hash
from ecosystems.afriride.runtime.commands import AssignDriver
from ecosystems.afriride.runtime.execution.deterministic_executor import (
    DeterministicExecutor,
)
from ecosystems.afriride.runtime.state import RideState

from afriride_system.backend.repositories import (
    DriverRepository,
    EventRepository,
    RideRepository,
)
from afriride_system.backend.state import DriverSession, RideSession
from afriride_system.integration.websocket_gateway.event_bridge import EventBridge


class AfriRidePhase1Error(RuntimeError):
    pass


@dataclass
class AfriRideCommandDispatcher:
    event_bridge: EventBridge
    driver_repository: DriverRepository
    ride_repository: RideRepository
    event_repository: EventRepository
    _mutation_lock: RLock = field(default_factory=RLock, repr=False)

    @property
    def drivers(self) -> dict[str, DriverSession]:
        return {
            driver.driver_id: driver
            for driver in self.driver_repository.all()
        }

    @property
    def rides(self) -> dict[str, RideSession]:
        return {
            ride.ride_id: ride
            for ride in self.ride_repository.all()
        }

    def set_driver_status(self, driver_id: str, online: bool) -> dict[str, Any]:
        with self._mutation_lock:
            session = DriverSession(driver_id=driver_id, online=online)
            self.driver_repository.save(session)
            return {"driver_id": driver_id, "online": online}

    def request_ride(
        self,
        *,
        passenger_id: str,
        pickup: str,
        destination: str,
        ride_id: str | None = None,
    ) -> dict[str, Any]:
        with self._mutation_lock:
            resolved_ride_id = ride_id or f"ride-{uuid4().hex[:8]}"
            if resolved_ride_id in self.rides:
                raise AfriRidePhase1Error("ride_already_exists")

            ride = RideSession(
                ride_id=resolved_ride_id,
                passenger_id=passenger_id,
                pickup=pickup,
                destination=destination,
                events=("ride_requested",),
            )
            self.ride_repository.save(ride)
            self.event_repository.append(
                ride.ride_id,
                "ride_requested",
                ride.snapshot(),
            )
            return ride.snapshot()

    def driver_requests(self, driver_id: str) -> list[dict[str, Any]]:
        driver = self.driver_repository.get(driver_id)
        if driver is None or not driver.online:
            return []

        return [
            ride.snapshot()
            for ride in self.ride_repository.all()
            if ride.status == "REQUESTED"
        ]

    def accept_ride(
        self,
        *,
        driver_id: str,
        ride_id: str,
        epoch: int = 6,
    ) -> dict[str, Any]:
        with self._mutation_lock:
            ride = self._require_ride(ride_id)
            driver = self.driver_repository.get(driver_id)

            if driver is None or not driver.online:
                raise AfriRidePhase1Error("driver_not_online")
            if ride.status != "REQUESTED":
                raise AfriRidePhase1Error("ride_not_accepting_driver")

            trace, final_state = DeterministicExecutor.execute_with_state(
                state=self._assignment_state(),
                commands=(AssignDriver(driver_id=driver_id, epoch=epoch),),
                epoch=epoch,
            )
            final_snapshot = final_state.snapshot()

            if final_snapshot["assigned_driver"] != driver_id:
                raise AfriRidePhase1Error("driver_assignment_refused")

            updated = ride.with_update(
                status="DRIVER_ASSIGNED",
                assigned_driver=driver_id,
                trace_hash=DeterministicExecutor.trace_hash(trace),
                state_hash=canonical_hash(final_snapshot),
                events=(*ride.events, "driver_assigned"),
            )
            self.ride_repository.save(updated)
            self.event_repository.append(
                ride_id,
                "driver_assigned",
                updated.snapshot(),
            )
            self.event_bridge.publish(
                f"ride_updates:{ride_id}",
                "driver_assigned",
                updated.snapshot(),
            )
            self.event_bridge.publish(
                f"driver_updates:{driver_id}",
                "driver_assigned",
                updated.snapshot(),
            )
            return updated.snapshot()

    def start_trip(self, *, driver_id: str, ride_id: str) -> dict[str, Any]:
        with self._mutation_lock:
            ride = self._require_driver_ride(driver_id, ride_id)
            if ride.status != "DRIVER_ARRIVED":
                raise AfriRidePhase1Error("trip_not_ready_to_start")

            updated = ride.with_update(
                status="IN_TRIP",
                events=(*ride.events, "trip_started"),
            )
            self.ride_repository.save(updated)
            self.event_repository.append(
                ride_id,
                "trip_started",
                updated.snapshot(),
            )
            self.event_bridge.publish(
                f"ride_updates:{ride_id}",
                "trip_started",
                updated.snapshot(),
            )
            return updated.snapshot()

    def arrive_trip(self, *, driver_id: str, ride_id: str) -> dict[str, Any]:
        with self._mutation_lock:
            ride = self._require_driver_ride(driver_id, ride_id)
            if ride.status != "DRIVER_ASSIGNED":
                raise AfriRidePhase1Error("trip_not_ready_to_arrive")

            updated = ride.with_update(
                status="DRIVER_ARRIVED",
                events=(*ride.events, "driver_arrived"),
            )
            self.ride_repository.save(updated)
            self.event_repository.append(
                ride_id,
                "driver_arrived",
                updated.snapshot(),
            )
            self.event_bridge.publish(
                f"ride_updates:{ride_id}",
                "driver_arrived",
                updated.snapshot(),
            )
            return updated.snapshot()

    def complete_trip(self, *, driver_id: str, ride_id: str) -> dict[str, Any]:
        with self._mutation_lock:
            ride = self._require_driver_ride(driver_id, ride_id)
            if ride.status != "IN_TRIP":
                raise AfriRidePhase1Error("trip_not_in_progress")

            updated = ride.with_update(
                status="COMPLETED",
                events=(*ride.events, "trip_completed"),
            )
            self.ride_repository.save(updated)
            self.event_repository.append(
                ride_id,
                "trip_completed",
                updated.snapshot(),
            )
            self.event_bridge.publish(
                f"ride_updates:{ride_id}",
                "trip_completed",
                updated.snapshot(),
            )
            return updated.snapshot()

    def cancel_ride(self, *, passenger_id: str, ride_id: str) -> dict[str, Any]:
        with self._mutation_lock:
            ride = self._require_ride(ride_id)
            if ride.passenger_id != passenger_id:
                raise AfriRidePhase1Error("passenger_mismatch")
            if ride.status in {"IN_TRIP", "COMPLETED"}:
                raise AfriRidePhase1Error("ride_not_cancelable")

            updated = ride.with_update(
                status="CANCELED",
                events=(*ride.events, "ride_canceled"),
            )
            self.ride_repository.save(updated)
            self.event_repository.append(
                ride_id,
                "ride_canceled",
                updated.snapshot(),
            )
            return updated.snapshot()

    def ride_status(self, ride_id: str) -> dict[str, Any]:
        return self._require_ride(ride_id).snapshot()

    def _require_ride(self, ride_id: str) -> RideSession:
        ride = self.ride_repository.get(ride_id)
        if ride is None:
            raise AfriRidePhase1Error("ride_not_found")
        return ride

    def _require_driver_ride(self, driver_id: str, ride_id: str) -> RideSession:
        ride = self._require_ride(ride_id)
        if ride.assigned_driver != driver_id:
            raise AfriRidePhase1Error("driver_not_assigned_to_ride")
        return ride

    def _assignment_state(self) -> RideState:
        return RideState(
            drivers_available=frozenset(
                driver_id
                for driver_id, driver in self.drivers.items()
                if driver.online
            ),
            ride_status="OPEN",
            assigned_driver=None,
            ride_a_assigned=None,
            ride_b_assigned=None,
        )
