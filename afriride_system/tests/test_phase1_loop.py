from afriride_system.backend.api_gateway.gateway import build_gateway
from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRidePhase1Error,
)
from afriride_system.clients.driver_app.client import DriverApp
from afriride_system.clients.passenger_app.client import PassengerApp


def test_passenger_driver_trip_completes_with_replay_hashes() -> None:
    gateway = build_gateway(reset=True)
    passenger = PassengerApp("passenger-1", gateway.passenger)
    driver = DriverApp("A", gateway.driver)

    assert driver.go_online() == {"driver_id": "A", "online": True}

    requested = passenger.request_ride(
        pickup="Kampala Road",
        destination="Nakasero",
        ride_id="ride-phase-1",
    )
    assert requested["status"] == "REQUESTED"

    pending = driver.requests()
    assert [ride["ride_id"] for ride in pending] == ["ride-phase-1"]

    accepted = driver.accept("ride-phase-1")
    assert accepted["status"] == "DRIVER_ASSIGNED"
    assert accepted["assigned_driver"] == "A"
    assert accepted["trace_hash"]
    assert accepted["state_hash"]

    arrived = driver.arrive("ride-phase-1")
    assert arrived["status"] == "DRIVER_ARRIVED"

    started = driver.start("ride-phase-1")
    assert started["status"] == "IN_TRIP"

    completed = driver.complete("ride-phase-1")
    assert completed["status"] == "COMPLETED"
    assert completed["events"] == [
        "ride_requested",
        "driver_assigned",
        "driver_arrived",
        "trip_started",
        "trip_completed",
    ]

    passenger_view = passenger.status("ride-phase-1")
    assert passenger_view == completed

    event_types = [
        event.event_type
        for event in gateway.event_bridge.events_for("ride_updates:ride-phase-1")
    ]
    assert event_types == [
        "driver_assigned",
        "driver_arrived",
        "trip_started",
        "trip_completed",
    ]


def test_illegal_transition_is_rejected() -> None:
    gateway = build_gateway(reset=True)
    passenger = PassengerApp("passenger-1", gateway.passenger)
    driver = DriverApp("A", gateway.driver)

    driver.go_online()
    passenger.request_ride(
        pickup="Kampala Road",
        destination="Nakasero",
        ride_id="ride-illegal",
    )

    try:
        driver.complete("ride-illegal")
    except AfriRidePhase1Error as exc:
        assert str(exc) == "driver_not_assigned_to_ride"
    else:
        raise AssertionError("illegal transition was accepted")
