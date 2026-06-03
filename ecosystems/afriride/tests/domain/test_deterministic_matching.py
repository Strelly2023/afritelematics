import pytest

from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_matching import (
    MatchingViolation,
    match_driver,
    rank_driver_candidates,
)


def ride():
    return Ride(
        id="RIDE-001",
        passenger_id="PASSENGER-001",
        pickup_location={"zone": "ZONE-A", "lat": 0.0, "lng": 0.0},
        dropoff_location={"zone": "ZONE-B", "lat": 1.0, "lng": 1.0},
        requested_at="2026-05-25T09:00:00Z",
    )


def test_matching_selects_nearest_same_partition_driver():
    assignment = match_driver(
        ride(),
        [
            {"id": "DRIVER-002", "zone": "ZONE-A", "lat": 0.2, "lng": 0.0},
            {"id": "DRIVER-001", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0},
        ],
    )

    assert assignment is not None
    assert assignment.driver_id == "DRIVER-001"
    assert assignment.ride_partition == "ZONE-A"
    assert assignment.driver_partition == "ZONE-A"
    assert assignment.locality == "same_partition"


def test_matching_uses_driver_id_as_stable_tie_breaker():
    assignment = match_driver(
        ride(),
        [
            {"id": "DRIVER-B", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0},
            {"id": "DRIVER-A", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0},
        ],
    )

    assert assignment.driver_id == "DRIVER-A"


def test_matching_rejects_cross_partition_by_default():
    assignment = match_driver(
        ride(),
        [
            {"id": "DRIVER-001", "zone": "ZONE-B", "lat": 0.01, "lng": 0.0},
        ],
    )

    assert assignment is None


def test_matching_allows_declared_cross_partition_candidate_after_locality():
    assignment = match_driver(
        ride(),
        [
            {"id": "DRIVER-REMOTE", "zone": "ZONE-B", "lat": 0.01, "lng": 0.0},
            {"id": "DRIVER-LOCAL", "zone": "ZONE-A", "lat": 0.5, "lng": 0.0},
        ],
        allow_cross_partition=True,
    )

    assert assignment.driver_id == "DRIVER-LOCAL"
    assert assignment.locality == "same_partition"


def test_matching_can_select_cross_partition_when_declared_and_only_candidate():
    assignment = match_driver(
        ride(),
        [
            {"id": "DRIVER-REMOTE", "zone": "ZONE-B", "lat": 0.01, "lng": 0.0},
        ],
        allow_cross_partition=True,
    )

    assert assignment.driver_id == "DRIVER-REMOTE"
    assert assignment.locality == "declared_cross_partition"


def test_matching_ranking_is_deterministic():
    ranked = rank_driver_candidates(
        ride(),
        [
            {"id": "DRIVER-C", "zone": "ZONE-A", "lat": 0.3, "lng": 0.0},
            {"id": "DRIVER-A", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0},
            {"id": "DRIVER-B", "zone": "ZONE-A", "lat": 0.2, "lng": 0.0},
        ],
    )

    assert [assignment.driver_id for assignment in ranked] == [
        "DRIVER-A",
        "DRIVER-B",
        "DRIVER-C",
    ]


def test_matching_assignment_representation_is_stable():
    assignment = match_driver(
        ride(),
        [{"id": "DRIVER-001", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0}],
    )

    assert assignment.canonical_json() == assignment.canonical_json()
    assert assignment.assignment_hash() == assignment.assignment_hash()
    assert assignment.to_canonical_dict()["score"] == [0, 0.1, "DRIVER-001"]


@pytest.mark.parametrize(
    "driver",
    [
        {"zone": "ZONE-A", "lat": 0.0, "lng": 0.0},
        {"id": "DRIVER-001", "lat": 0.0, "lng": 0.0},
        {"id": "DRIVER-001", "zone": "ZONE-A", "lat": "0", "lng": 0.0},
    ],
)
def test_matching_rejects_undeclared_driver_inputs(driver):
    with pytest.raises(MatchingViolation):
        match_driver(ride(), [driver])
