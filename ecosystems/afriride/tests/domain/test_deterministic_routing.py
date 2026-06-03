import pytest

from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_routing import (
    RoutingViolation,
    canonical_graph_json,
    compute_route,
)


def ride(**overrides):
    payload = {
        "id": "RIDE-001",
        "passenger_id": "PASSENGER-001",
        "pickup_location": {"zone": "ZONE-A", "node_id": "A", "lat": 0.0, "lng": 0.0},
        "dropoff_location": {"zone": "ZONE-B", "node_id": "D", "lat": 1.0, "lng": 1.0},
        "requested_at": "2026-05-25T09:00:00Z",
    }
    payload.update(overrides)
    return Ride(**payload)


def graph(**overrides):
    payload = {
        "nodes": {
            "A": {"zone": "ZONE-A"},
            "B": {"zone": "ZONE-A"},
            "C": {"zone": "ZONE-B"},
            "D": {"zone": "ZONE-B"},
        },
        "edges": [
            {"from": "A", "to": "B", "distance": 1.0, "estimated_time": 2.0},
            {"from": "B", "to": "D", "distance": 1.0, "estimated_time": 2.0},
            {"from": "A", "to": "C", "distance": 1.0, "estimated_time": 5.0},
            {"from": "C", "to": "D", "distance": 1.0, "estimated_time": 1.0},
            {"from": "A", "to": "D", "distance": 3.0, "estimated_time": 3.0},
        ],
    }
    payload.update(overrides)
    return payload


def test_routing_computes_shortest_declared_path():
    route = compute_route(ride(), graph())

    assert route.path == ("A", "B", "D")
    assert route.distance == 2.0
    assert route.estimated_time == 4.0
    assert route.cost_basis == "distance_then_time_then_path"


def test_routing_uses_time_as_stable_secondary_score():
    route = compute_route(
        ride(),
        graph(
            edges=[
                {"from": "A", "to": "B", "distance": 1.0, "estimated_time": 4.0},
                {"from": "B", "to": "D", "distance": 1.0, "estimated_time": 4.0},
                {"from": "A", "to": "C", "distance": 1.0, "estimated_time": 1.0},
                {"from": "C", "to": "D", "distance": 1.0, "estimated_time": 1.0},
            ]
        ),
    )

    assert route.path == ("A", "C", "D")
    assert route.distance == 2.0
    assert route.estimated_time == 2.0


def test_routing_uses_path_as_final_stable_tie_breaker():
    route = compute_route(
        ride(),
        graph(
            edges=[
                {"from": "A", "to": "C", "distance": 1.0, "estimated_time": 1.0},
                {"from": "C", "to": "D", "distance": 1.0, "estimated_time": 1.0},
                {"from": "A", "to": "B", "distance": 1.0, "estimated_time": 1.0},
                {"from": "B", "to": "D", "distance": 1.0, "estimated_time": 1.0},
            ]
        ),
    )

    assert route.path == ("A", "B", "D")


def test_routing_representation_is_stable():
    route = compute_route(ride(), graph())

    assert route.canonical_json() == route.canonical_json()
    assert route.route_hash() == route.route_hash()
    assert canonical_graph_json(graph()) == canonical_graph_json(
        {
            "edges": list(reversed(graph()["edges"])),
            "nodes": {
                "D": {"zone": "ZONE-B"},
                "C": {"zone": "ZONE-B"},
                "B": {"zone": "ZONE-A"},
                "A": {"zone": "ZONE-A"},
            },
        }
    )


@pytest.mark.parametrize(
    "pickup_location,dropoff_location",
    [
        ({"zone": "ZONE-A", "lat": 0.0, "lng": 0.0}, {"zone": "ZONE-B", "node_id": "D"}),
        ({"zone": "ZONE-A", "node_id": "A"}, {"zone": "ZONE-B", "lat": 1.0}),
    ],
)
def test_routing_requires_declared_endpoint_nodes(pickup_location, dropoff_location):
    with pytest.raises(RoutingViolation):
        compute_route(
            ride(pickup_location=pickup_location, dropoff_location=dropoff_location),
            graph(),
        )


def test_routing_rejects_disconnected_graph():
    with pytest.raises(RoutingViolation):
        compute_route(
            ride(),
            graph(edges=[{"from": "A", "to": "B", "distance": 1.0, "estimated_time": 1.0}]),
        )


@pytest.mark.parametrize(
    "bad_graph",
    [
        {"nodes": {}, "edges": []},
        {"nodes": {"A": {}, "D": {}}, "edges": "A-D"},
        {
            "nodes": {"A": {}, "D": {}},
            "edges": [{"from": "A", "to": "D", "distance": -1, "estimated_time": 1}],
        },
        {
            "nodes": {"A": {}, "D": {}},
            "edges": [{"from": "A", "to": "X", "distance": 1, "estimated_time": 1}],
        },
    ],
)
def test_routing_rejects_undeclared_graph_inputs(bad_graph):
    with pytest.raises(RoutingViolation):
        compute_route(ride(), bad_graph)
