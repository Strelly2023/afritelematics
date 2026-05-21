from __future__ import annotations

import pytest

from afritech.core.matching_engine import match_driver


def test_matching_engine_selects_highest_deterministic_score() -> None:
    request = {"request_id": "ride-001"}
    drivers = [
        {
            "driver_id": "driver-b",
            "distance_km": "2.5",
            "rating": "4.9",
            "active_trips": 0,
        },
        {
            "driver_id": "driver-a",
            "distance_km": "1.1",
            "rating": "4.7",
            "active_trips": 0,
        },
    ]

    result = match_driver(request, drivers)

    assert result["selected_driver_id"] == "driver-a"
    assert [entry["driver_id"] for entry in result["ranking"]] == [
        "driver-a",
        "driver-b",
    ]
    assert result["matching_policy"] == "distance_rating_active_trips_v1"


def test_matching_engine_uses_driver_id_tie_breaker() -> None:
    request = {"request_id": "ride-002"}
    drivers = [
        {
            "driver_id": "driver-a",
            "distance_km": "1.0",
            "rating": "5.0",
            "active_trips": 0,
        },
        {
            "driver_id": "driver-b",
            "distance_km": "1.0",
            "rating": "5.0",
            "active_trips": 0,
        },
    ]

    result = match_driver(request, drivers)

    assert result["selected_driver_id"] == "driver-b"
    assert [entry["driver_id"] for entry in result["ranking"]] == [
        "driver-b",
        "driver-a",
    ]


def test_matching_engine_is_replay_stable_for_input_order() -> None:
    request = {"request_id": "ride-003"}
    first_order = [
        {
            "driver_id": "driver-c",
            "distance_km": "2.0",
            "rating": "4.8",
            "active_trips": 1,
        },
        {
            "driver_id": "driver-d",
            "distance_km": "1.9",
            "rating": "4.7",
            "active_trips": 0,
        },
    ]
    second_order = list(reversed(first_order))

    assert match_driver(request, first_order) == match_driver(request, second_order)


def test_matching_engine_rejects_missing_candidates() -> None:
    with pytest.raises(ValueError, match="at least one candidate"):
        match_driver({"request_id": "ride-004"}, [])


def test_matching_engine_rejects_negative_distance() -> None:
    with pytest.raises(ValueError, match="distance_km must be non-negative"):
        match_driver(
            {"request_id": "ride-005"},
            [
                {
                    "driver_id": "driver-x",
                    "distance_km": "-1",
                    "rating": "5.0",
                    "active_trips": 0,
                }
            ],
        )
