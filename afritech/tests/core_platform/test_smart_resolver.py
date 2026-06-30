from __future__ import annotations

from afritech.core_platform.smart_resolver import resolve_smart_offline_navigation


def test_smart_resolver_dead_reckons_when_gps_and_network_are_lost() -> None:
    result = resolve_smart_offline_navigation(
        ride_id="ride-123",
        driver_id="driver-123",
        location={
            "lat": -37.8136,
            "lon": 144.9631,
            "heading_deg": 90,
            "speed_kph": 60,
            "label": "Melbourne CBD",
        },
        route_context={
            "waypoints": [
                {"name": "pickup", "lat": -37.8136, "lon": 144.9631, "status": "pending"},
                {"name": "destination", "lat": -37.8200, "lon": 144.9500, "status": "pending"},
            ]
        },
        connectivity={"gps": False, "network": False, "internet": False, "cached_route": True},
        telemetry={"sample_age_seconds": 120},
    )

    assert result["mode"] == "offline_continuity"
    assert result["action"] == "dead_reckon_and_hold_sync"
    assert result["location"]["source"] == "dead_reckoning"
    assert result["sync"]["queue_locally"] is True
    assert result["safety"]["allow_trip_continue"] is True
    assert result["confidence"] < 0.8
    assert result["route"]["next_waypoint"]["name"] == "pickup"


def test_smart_resolver_handover_when_no_gps_and_no_cached_route() -> None:
    result = resolve_smart_offline_navigation(
        ride_id="ride-124",
        driver_id="driver-124",
        location={"lat": -37.8136, "lon": 144.9631},
        connectivity={"gps": False, "network": False, "internet": False, "cached_route": False},
        telemetry={"sample_age_seconds": 20},
    )

    assert result["mode"] == "offline_handover"
    assert result["action"] == "hold_position_and_request_manual_checkin"
    assert result["safety"]["allow_trip_continue"] is False
    assert result["safety"]["require_manual_review"] is True
