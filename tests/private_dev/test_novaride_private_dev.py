from __future__ import annotations

import pytest

from tests.private_dev._helpers import assert_contains_all, read_json, read_text


pytestmark = [pytest.mark.private_dev, pytest.mark.novaride]


def test_novaride_rider_driver_and_operator_surfaces_exist() -> None:
    registry = read_json("docs/mobile/private_dev_button_registry.json")["apps"]

    for app_key in ("novaride_rider", "novaride_driver", "novaride_operator"):
        spec = registry[app_key]
        source = read_text(spec["source"])
        assert_contains_all(source, list(spec["tabs"]), context=f"{app_key} tabs")
        assert_contains_all(source, list(spec["buttons"]), context=f"{app_key} buttons")


def test_novaride_driver_flow_exposes_request_queue_and_trip_actions() -> None:
    source = read_text("driver_app/state/providers/useDriverFlow.ts")
    assert "getRideRequests(driverId)" in source
    assert "/v1/driver/${encodeURIComponent(driverId)}/ride-queue" in read_text(
        "driver_app/core/api/driver.service.ts"
    )
    assert "/v1/driver/rides/${encodeURIComponent(rideId)}/accept" in read_text(
        "driver_app/core/api/driver.service.ts"
    )
    assert "/v1/rider/rides" in read_text("rider_app/core/api/ride.service.ts")

