from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.driver_routes import (
    accept_ride,
    arrive_trip,
    complete_trip,
    driver_requests,
    driver_status,
    start_trip,
)
from afriride_system.api.passenger_routes import request_ride, ride_status
from afriride_system.api.schemas import DriverStatus, RequestRide, RideAction


def test_fastapi_full_ride_flow() -> None:
    gateway = reset_gateway()

    status_response = driver_status(
        DriverStatus(driver_id="A", online=True),
        idempotency_key="driver-online-api-1",
        gateway=gateway,
    )
    assert status_response["status"] == "success"
    assert status_response["data"] == {"driver_id": "A", "online": True}
    assert status_response["error"] is None

    requested = request_ride(
        RequestRide(
            passenger_id="passenger-1",
            pickup="Kampala Road",
            destination="Nakasero",
            ride_id="ride-api-1",
        ),
        idempotency_key="request-api-1",
        gateway=gateway,
    )
    assert requested["data"]["status"] == "REQUESTED"

    duplicate_request = request_ride(
        RequestRide(
            passenger_id="passenger-1",
            pickup="Kampala Road",
            destination="Nakasero",
            ride_id="ride-api-1",
        ),
        idempotency_key="request-api-1",
        gateway=gateway,
    )
    assert duplicate_request == requested

    pending = driver_requests("A", gateway=gateway)
    assert [ride["ride_id"] for ride in pending["data"]] == ["ride-api-1"]

    accepted = accept_ride(
        RideAction(driver_id="A", ride_id="ride-api-1"),
        idempotency_key="accept-api-1",
        gateway=gateway,
    )
    assert accepted["data"]["status"] == "DRIVER_ASSIGNED"
    assert accepted["data"]["trace_hash"]

    duplicate_accept = accept_ride(
        RideAction(driver_id="A", ride_id="ride-api-1"),
        idempotency_key="accept-api-1",
        gateway=gateway,
    )
    assert duplicate_accept == accepted

    arrived = arrive_trip(
        RideAction(driver_id="A", ride_id="ride-api-1"),
        idempotency_key="arrive-api-1",
        gateway=gateway,
    )
    assert arrived["data"]["status"] == "DRIVER_ARRIVED"

    started = start_trip(
        RideAction(driver_id="A", ride_id="ride-api-1"),
        idempotency_key="start-api-1",
        gateway=gateway,
    )
    assert started["data"]["status"] == "IN_TRIP"

    completed = complete_trip(
        RideAction(driver_id="A", ride_id="ride-api-1"),
        idempotency_key="complete-api-1",
        gateway=gateway,
    )
    assert completed["data"]["status"] == "COMPLETED"

    passenger_status = ride_status("ride-api-1", gateway=gateway)
    assert passenger_status["data"] == completed["data"]


def test_fastapi_rejects_illegal_transition() -> None:
    gateway = reset_gateway()

    try:
        complete_trip(
            RideAction(driver_id="A", ride_id="missing"),
            idempotency_key="missing-complete",
            gateway=gateway,
        )
    except Exception as exc:
        assert getattr(exc, "status_code") == 400
        assert getattr(exc, "detail") == "ride_not_found"
    else:
        raise AssertionError("missing ride was accepted")
