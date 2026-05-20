from __future__ import annotations

from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.driver_routes import driver_status
from afriride_system.api.passenger_routes import request_ride, ride_status
from afriride_system.api.schemas import DriverStatus, RequestRide


def test_request_ride_rejects_idempotency_key_reused_with_different_payload() -> None:
    gateway = reset_gateway()

    first = request_ride(
        RequestRide(
            passenger_id="passenger-1",
            pickup="Kampala Road",
            destination="Nakasero",
            ride_id="ride-idempotency-1",
        ),
        idempotency_key="request-key-1",
        gateway=gateway,
    )

    try:
        request_ride(
            RequestRide(
                passenger_id="passenger-1",
                pickup="Kampala Road",
                destination="Kololo",
                ride_id="ride-idempotency-2",
            ),
            idempotency_key="request-key-1",
            gateway=gateway,
        )
    except Exception as exc:
        assert getattr(exc, "status_code") == 409
        assert getattr(exc, "detail") == (
            "idempotency_key_reused_with_different_payload"
        )
    else:
        raise AssertionError("conflicting idempotent request was accepted")

    assert ride_status("ride-idempotency-1", gateway=gateway)["data"] == first["data"]

    try:
        ride_status("ride-idempotency-2", gateway=gateway)
    except Exception as exc:
        assert getattr(exc, "status_code") == 404
        assert getattr(exc, "detail") == "ride_not_found"
    else:
        raise AssertionError("conflicting idempotent request mutated ride state")


def test_driver_status_rejects_idempotency_key_reused_with_different_payload() -> None:
    gateway = reset_gateway()

    first = driver_status(
        DriverStatus(driver_id="driver-1", online=True),
        idempotency_key="driver-status-key-1",
        gateway=gateway,
    )

    duplicate = driver_status(
        DriverStatus(driver_id="driver-1", online=True),
        idempotency_key="driver-status-key-1",
        gateway=gateway,
    )

    assert duplicate == first

    try:
        driver_status(
            DriverStatus(driver_id="driver-1", online=False),
            idempotency_key="driver-status-key-1",
            gateway=gateway,
        )
    except Exception as exc:
        assert getattr(exc, "status_code") == 409
        assert getattr(exc, "detail") == (
            "idempotency_key_reused_with_different_payload"
        )
    else:
        raise AssertionError("conflicting idempotent driver update was accepted")
