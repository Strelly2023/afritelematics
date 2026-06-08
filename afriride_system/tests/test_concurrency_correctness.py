from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.passenger_routes import request_ride
from afriride_system.api.schemas import RequestRide
from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRidePhase1Error,
)


def test_concurrent_idempotent_request_returns_single_authoritative_result() -> None:
    gateway = reset_gateway()
    barrier = Barrier(2)

    def invoke() -> dict:
        barrier.wait()
        return request_ride(
            RequestRide(
                passenger_id="rider-concurrent-1",
                pickup="Point A",
                destination="Point B",
                ride_id="ride-concurrent-idempotent-1",
            ),
            idempotency_key="request-concurrency-key-1",
            gateway=gateway,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = tuple(executor.map(lambda _: invoke(), range(2)))

    assert first == second
    rides = gateway.dispatcher.rides
    assert tuple(rides) == ("ride-concurrent-idempotent-1",)
    assert rides["ride-concurrent-idempotent-1"].status == "REQUESTED"


def test_concurrent_idempotency_conflict_allows_only_one_payload() -> None:
    gateway = reset_gateway()
    barrier = Barrier(2)
    outcomes: list[tuple[str, str]] = []

    def invoke(ride_id: str, destination: str) -> None:
        barrier.wait()
        try:
            result = request_ride(
                RequestRide(
                    passenger_id="rider-concurrent-2",
                    pickup="Point A",
                    destination=destination,
                    ride_id=ride_id,
                ),
                idempotency_key="request-concurrency-key-2",
                gateway=gateway,
            )
        except Exception as exc:  # route helper raises HTTPException
            outcomes.append(("error", getattr(exc, "detail")))
            return
        outcomes.append(("ok", result["data"]["ride_id"]))

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = (
            executor.submit(invoke, "ride-concurrent-conflict-1", "Point B"),
            executor.submit(invoke, "ride-concurrent-conflict-2", "Point C"),
        )
        for future in futures:
            future.result()

    assert len(outcomes) == 2
    assert sum(1 for kind, _ in outcomes if kind == "ok") == 1
    assert sum(1 for kind, detail in outcomes if kind == "error" and detail == "idempotency_key_reused_with_different_payload") == 1
    assert len(gateway.dispatcher.rides) == 1


def test_concurrent_accept_selects_single_driver() -> None:
    gateway = reset_gateway()
    gateway.driver.status({"driver_id": "driver-concurrent-a", "online": True})
    gateway.driver.status({"driver_id": "driver-concurrent-b", "online": True})
    gateway.passenger.request_ride(
        {
            "passenger_id": "rider-concurrent-3",
            "pickup": "Point A",
            "destination": "Point B",
            "ride_id": "ride-concurrent-accept-1",
        }
    )

    barrier = Barrier(2)
    outcomes: list[tuple[str, str]] = []

    def invoke(driver_id: str) -> None:
        barrier.wait()
        try:
            result = gateway.driver.accept(
                {"driver_id": driver_id, "ride_id": "ride-concurrent-accept-1"}
            )
        except AfriRidePhase1Error as exc:
            outcomes.append(("error", str(exc)))
            return
        outcomes.append(("ok", result["assigned_driver"]))

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = (
            executor.submit(invoke, "driver-concurrent-a"),
            executor.submit(invoke, "driver-concurrent-b"),
        )
        for future in futures:
            future.result()

    assert len(outcomes) == 2
    successes = [value for kind, value in outcomes if kind == "ok"]
    errors = [value for kind, value in outcomes if kind == "error"]
    assert len(successes) == 1
    assert errors == ["ride_not_accepting_driver"]

    ride = gateway.dispatcher.rides["ride-concurrent-accept-1"]
    assert ride.status == "DRIVER_ASSIGNED"
    assert ride.assigned_driver == successes[0]
    assert ride.events == ("ride_requested", "driver_assigned")
