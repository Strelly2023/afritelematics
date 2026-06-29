from __future__ import annotations

from afritech.dispatch.matching import select_driver_for_ride


def test_dispatch_prefers_fresher_driver_when_trust_and_distance_match() -> None:
    ride = {
        "ride_id": "ride-001",
        "pickup_location": {"lat": -37.8136, "lng": 144.9631},
        "destination_location": {"lat": -37.8200, "lng": 144.9500},
    }
    now = 1_700_000_000
    driver_presence = [
        {
            "driver_id": "driver-stale",
            "status": "online",
            "location": {"lat": -37.8136, "lng": 144.9631, "timestamp": now - 240},
            "trust_score": 92.0,
            "last_seen": now - 240,
            "metadata": {},
        },
        {
            "driver_id": "driver-fresh",
            "status": "online",
            "location": {"lat": -37.8136, "lng": 144.9631, "timestamp": now},
            "trust_score": 92.0,
            "last_seen": now,
            "metadata": {},
        },
    ]

    decision = select_driver_for_ride(ride=ride, driver_presence=driver_presence)

    assert decision is not None
    assert decision["selected_driver_id"] == "driver-fresh"
    ranked = decision["ranked_candidates"]
    assert ranked[0]["participant_id"] == "driver-fresh"
    assert ranked[0]["reliability_score"] >= ranked[1]["reliability_score"]
    assert ranked[0]["anomaly_rate"] <= ranked[1]["anomaly_rate"]


def test_dispatch_excludes_busy_driver_even_with_higher_trust() -> None:
    ride = {
        "ride_id": "ride-002",
        "pickup_location": {"lat": -37.8136, "lng": 144.9631},
        "destination_location": {"lat": -37.8200, "lng": 144.9500},
    }
    now = 1_700_000_000
    driver_presence = [
        {
            "driver_id": "driver-busy",
            "status": "online",
            "location": {"lat": -37.8136, "lng": 144.9631, "timestamp": now},
            "trust_score": 98.0,
            "last_seen": now,
            "busy_ride_id": "ride-active",
            "metadata": {},
        },
        {
            "driver_id": "driver-idle",
            "status": "online",
            "location": {"lat": -37.8136, "lng": 144.9631, "timestamp": now},
            "trust_score": 91.0,
            "last_seen": now,
            "metadata": {},
        },
    ]

    decision = select_driver_for_ride(ride=ride, driver_presence=driver_presence)

    assert decision is not None
    assert decision["selected_driver_id"] == "driver-idle"
    assert all(candidate["participant_id"] != "driver-busy" for candidate in decision["ranked_candidates"])
