from __future__ import annotations

from afritech.ci import (
    client_replay_validator,
    geo_determinism_validator,
    scale_determinism_validator,
)
from afritech.simulation.validation_receipt import SCHEMA
from afritech.simulation.scale.cluster_simulator import (
    ClusterSimulator,
    hash_scale_trace,
)
from afritech.simulation.scale.failure_injector import FailureInjector
from afritech.simulation.scale.load_generator import LoadGenerator
from ecosystems.afriride.client.device_model import MobileEvent
from ecosystems.afriride.client.normalization import EventNormalizer
from ecosystems.afriride.client.replay_engine import ClientReplayEngine, hash_client_trace
from ecosystems.afriride.geo.drift_simulator import DriftSimulator
from ecosystems.afriride.geo.engine import GeoEngine, hash_geo_trace
from ecosystems.afriride.geo.traffic_model import TrafficModel
from ecosystems.afriride.geo.types import GeoPoint


def test_geo_engine_produces_replay_stable_trip_trace() -> None:
    start = GeoPoint(lat=-37.8136, lon=144.9631, timestamp=1_700_000_000)
    end = GeoPoint(lat=-37.6733, lon=144.8433, timestamp=1_700_001_800)
    engine = GeoEngine(seed=42)

    trace_a = engine.compute_trip(start, end, steps=10)
    trace_b = engine.compute_trip(start, end, steps=10)

    assert trace_a == trace_b
    assert hash_geo_trace(trace_a) == hash_geo_trace(trace_b)
    assert trace_a.route[0] == start
    assert trace_a.route[-1] == end


def test_geo_drift_and_traffic_models_are_seeded_and_stable() -> None:
    point = GeoPoint(lat=-1.2921, lon=36.8219, timestamp=1_700_000_123)

    drift = DriftSimulator()
    assert drift.apply_drift(point, seed=10) == drift.apply_drift(point, seed=10)

    traffic = TrafficModel()
    assert traffic.delay("segment-a", 60, seed=10) == traffic.delay(
        "segment-a",
        60,
        seed=10,
    )


def test_client_replay_normalizes_orders_and_deduplicates_events() -> None:
    events = [
        MobileEvent("device-a", "evt-003", 10_900, {"action": "complete"}),
        MobileEvent("device-a", "evt-001", 10_100, {"action": "request"}),
        MobileEvent("device-a", "evt-002", 10_500, {"action": "start"}),
        MobileEvent("device-a", "evt-002", 10_500, {"action": "start"}),
    ]

    engine = ClientReplayEngine()
    trace_a = engine.replay(events)
    trace_b = engine.replay(list(reversed(events)))

    assert trace_a == trace_b
    assert hash_client_trace(trace_a) == hash_client_trace(trace_b)
    assert [event["event_id"] for event in trace_a] == [
        "evt-001",
        "evt-002",
        "evt-003",
    ]


def test_client_clock_drift_normalization_is_deterministic() -> None:
    normalizer = EventNormalizer(bucket_size=1000)
    event = MobileEvent("device-a", "evt-001", 1_000_000 + 600_000, {"action": "ping"})

    normalized_a = normalizer.normalize(event)
    normalized_b = normalizer.normalize(event)

    assert normalized_a == normalized_b
    assert normalized_a["timestamp"] == 1600


def test_scale_simulation_survives_worker_loss_and_partition_merge() -> None:
    events = LoadGenerator().generate(1_000, seed=99)
    workers = tuple(f"worker-{index}" for index in range(10))
    survivors = FailureInjector().kill_workers(workers, percentage=0.4)
    cluster = ClusterSimulator(num_partitions=12)

    trace_a = cluster.execute(events, workers=survivors)
    trace_b = cluster.execute(events, workers=survivors)

    assert len(survivors) == 6
    assert hash_scale_trace(trace_a) == hash_scale_trace(trace_b)

    midpoint = len(events) // 2
    merged = cluster.merge(
        cluster.execute(events[:midpoint], workers=survivors),
        cluster.execute(events[midpoint:], workers=survivors),
    )

    assert hash_scale_trace(merged) == hash_scale_trace(trace_a)


def test_phase1_validators_pass() -> None:
    geo_determinism_validator.run()
    client_replay_validator.run()
    scale_determinism_validator.run()


def test_phase1_validators_emit_replay_stable_validation_receipts() -> None:
    geo_receipt_a = geo_determinism_validator.build_receipt()
    geo_receipt_b = geo_determinism_validator.build_receipt()
    client_receipt_a = client_replay_validator.build_receipt()
    client_receipt_b = client_replay_validator.build_receipt()
    scale_receipt_a = scale_determinism_validator.build_receipt()
    scale_receipt_b = scale_determinism_validator.build_receipt()

    for left, right in (
        (geo_receipt_a, geo_receipt_b),
        (client_receipt_a, client_receipt_b),
        (scale_receipt_a, scale_receipt_b),
    ):
        assert left.schema == SCHEMA
        assert left == right
        assert left.replay_hash == right.replay_hash
        assert left.deterministic is True
        assert left.replay_safe is True
        assert left.input_hash
        assert left.output_hash
        assert left.trace_hash
        assert left.evidence
