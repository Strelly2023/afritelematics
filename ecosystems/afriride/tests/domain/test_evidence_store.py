import pytest

from ecosystems.afriride.domain.evidence.evidence_store import (
    EvidenceStoreViolation,
    InMemoryRideEvidenceStore,
    RideEvidenceBundle,
)
from ecosystems.afriride.domain.execution.ride_execution_engine import (
    TransitionRequest,
    execute_lifecycle,
)
from ecosystems.afriride.domain.models.canonical_ride import Ride
from ecosystems.afriride.domain.optimization.deterministic_matching import match_driver
from ecosystems.afriride.domain.optimization.deterministic_pricing import (
    PricingConfig,
    compute_price,
)
from ecosystems.afriride.domain.optimization.deterministic_routing import compute_route
from ecosystems.afriride.domain.trace.ride_execution_trace import (
    build_ride_execution_trace,
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


def drivers():
    return (
        {"id": "DRIVER-001", "zone": "ZONE-A", "lat": 0.1, "lng": 0.0},
    )


def graph():
    return {
        "nodes": {"A": {"zone": "ZONE-A"}, "B": {}, "D": {"zone": "ZONE-B"}},
        "edges": [
            {"from": "A", "to": "B", "distance": 2.0, "estimated_time": 3.0},
            {"from": "B", "to": "D", "distance": 3.0, "estimated_time": 7.0},
        ],
    }


def pricing_config(**overrides):
    payload = {
        "base_fare": "4.00",
        "per_distance_rate": "1.50",
        "per_time_rate": "0.25",
        "currency": "AUD",
    }
    payload.update(overrides)
    return PricingConfig(**payload)


def execution_steps(declared_ride):
    return execute_lifecycle(
        declared_ride,
        (
            TransitionRequest(
                ride_hash=declared_ride.ride_hash(),
                current_state="REQUESTED",
                target_state="MATCHED",
            ),
        ),
    )


def evidence_bundle(config=None):
    declared_ride = ride()
    assignment = match_driver(declared_ride, drivers())
    route = compute_route(declared_ride, graph())
    config = config or pricing_config()
    price = compute_price(declared_ride, assignment, route, config)
    steps = execution_steps(declared_ride)
    trace = build_ride_execution_trace(
        declared_ride,
        assignment=assignment,
        route=route,
        price=price,
        execution_steps=steps,
    )
    return RideEvidenceBundle(
        ride=declared_ride,
        trace=trace,
        drivers=drivers(),
        map_graph=graph(),
        pricing_config=config,
        assignment=assignment,
        route=route,
        price=price,
        execution_steps=steps,
    )


def test_evidence_store_validates_before_store_and_on_read():
    store = InMemoryRideEvidenceStore()
    bundle = evidence_bundle()

    trace_hash = store.store(bundle)
    verified = store.get(trace_hash)

    assert verified.bundle.trace_hash() == trace_hash
    assert verified.replay_report.replay_valid is True
    assert verified.bundle.canonical_summary()["price_hash"] == bundle.price.price_hash()


def test_evidence_store_rejects_duplicate_trace_hash():
    store = InMemoryRideEvidenceStore()
    bundle = evidence_bundle()
    store.store(bundle)

    with pytest.raises(EvidenceStoreViolation):
        store.store(bundle)


def test_evidence_store_rejects_invalid_evidence_on_write():
    store = InMemoryRideEvidenceStore()
    bundle = evidence_bundle(config=pricing_config(base_fare="4.00"))
    invalid = RideEvidenceBundle(
        ride=bundle.ride,
        trace=bundle.trace,
        drivers=bundle.drivers,
        map_graph=bundle.map_graph,
        pricing_config=pricing_config(base_fare="9.00"),
        assignment=bundle.assignment,
        route=bundle.route,
        price=bundle.price,
        execution_steps=bundle.execution_steps,
    )

    with pytest.raises(EvidenceStoreViolation):
        store.store(invalid)


def test_evidence_store_replays_on_read_and_detects_corruption():
    store = InMemoryRideEvidenceStore()
    bundle = evidence_bundle()
    trace_hash = store.store(bundle)
    store.corrupt_for_test(trace_hash, pricing_config=pricing_config(base_fare="9.00"))

    with pytest.raises(EvidenceStoreViolation):
        store.get(trace_hash)


def test_evidence_store_lists_trace_hashes_without_claiming_truth():
    store = InMemoryRideEvidenceStore()
    trace_hash = store.store(evidence_bundle())

    assert store.list_trace_hashes() == (trace_hash,)
