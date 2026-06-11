from __future__ import annotations

from afritech.monitoring.realtime_anomaly_alerting import build_realtime_anomaly_alerts


HASH_A = "a" * 64


def test_realtime_anomaly_alerts_are_trace_linked_and_deterministic() -> None:
    events = {
        "replay_mismatches": 1,
        "validation_failures": 1,
    }

    first = build_realtime_anomaly_alerts(
        events,
        ride_id="ride-001",
        trace_id="trace-001",
        event_id="event-001",
        actor_id="driver-001",
        device_id="device-001",
        replay_hash=HASH_A,
        receipt_hash=HASH_A,
        opened_at="2026-06-08T00:00:00Z",
    )
    second = build_realtime_anomaly_alerts(
        events,
        ride_id="ride-001",
        trace_id="trace-001",
        event_id="event-001",
        actor_id="driver-001",
        device_id="device-001",
        replay_hash=HASH_A,
        receipt_hash=HASH_A,
        opened_at="2026-06-08T00:00:00Z",
    )

    assert first == second
    assert [alert.anomaly_type for alert in first] == [
        "validation_failure",
        "replay_mismatch",
    ]
    assert first[1].severity == "CRITICAL"
    assert first[0].evidence_pointer == "trace:trace-001:event:event-001:ride:ride-001"


def test_realtime_anomaly_alerts_return_empty_tuple_without_anomalies() -> None:
    alerts = build_realtime_anomaly_alerts(
        {},
        ride_id="ride-001",
        trace_id="trace-001",
        event_id="event-001",
        actor_id="driver-001",
        device_id="device-001",
        replay_hash=HASH_A,
        opened_at="2026-06-08T00:00:00Z",
    )

    assert alerts == ()
