from __future__ import annotations

from pathlib import Path

from afriride_system.backend.api_gateway.gateway import build_gateway


def test_ride_and_driver_state_survive_gateway_rebuild(tmp_path: Path) -> None:
    db_path = tmp_path / "afriride-pilot.sqlite3"

    first_gateway = build_gateway(db_path=db_path, reset=True)
    assert first_gateway.driver.status({"driver_id": "driver-persist", "online": True}) == {
        "driver_id": "driver-persist",
        "online": True,
    }

    requested = first_gateway.passenger.request_ride(
        {
            "passenger_id": "rider-persist",
            "pickup": "Kampala Road",
            "destination": "Nakasero",
            "ride_id": "ride-persist-1",
        }
    )
    assert requested["status"] == "REQUESTED"

    second_gateway = build_gateway(db_path=db_path, reset=False)

    assert second_gateway.driver.requests("driver-persist") == [
        requested
    ]
    assert second_gateway.passenger.status("ride-persist-1") == requested
