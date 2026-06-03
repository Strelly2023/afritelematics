from __future__ import annotations

from afriride.field_validation import EventBuffer, replay_field_trace
from afriride.field_validation.device_logger import DeviceLogger
from afriride.field_validation.field_proof import (
    REQUIRED_SCENARIOS,
    run_afriride_field_proof,
)
from afritech.ci.afriride_field_validator import validate


def test_afriride_field_proof_preserves_all_scenarios():
    report = run_afriride_field_proof()

    assert report.verified is True
    assert tuple(scenario.scenario for scenario in report.scenarios) == REQUIRED_SCENARIOS
    for scenario in report.scenarios:
        assert scenario.replay.replay_match is True
        assert scenario.replay.identity_match is True
        assert scenario.replay.pricing_match is True
        assert scenario.dispute_match is True


def test_afriride_field_validator_accepts_generated_reports():
    report = validate()

    assert report.verified is True
    assert report.scenarios == REQUIRED_SCENARIOS


def test_offline_device_buffer_replays_to_clean_baseline():
    baseline = _trace()
    driver = DeviceLogger(device_id="driver.device.test", role="driver")
    buffer = EventBuffer()
    for event in baseline:
        online = int(event["sequence"]) < 3 or int(event["sequence"]) == 6
        buffer = buffer.append(
            driver.record(
                event,
                online=online,
                observed_at=f"2026-05-27T00:03:{int(event['sequence']):02d}Z",
            )
        )

    result = replay_field_trace(baseline, buffer.synced_events())

    assert result.verified is True


def test_gps_drift_is_observational_not_pricing_authority():
    baseline = _trace()
    field = (
        *baseline[:4],
        _gps_event(30, -37.8136, 144.9631),
        _gps_event(31, -37.9000, 145.2000),
        *baseline[4:],
    )
    result = replay_field_trace(baseline, field)

    assert result.pricing_match is True
    assert result.replay_match is True
    assert result.observed_event_count == len(baseline) + 2


def test_duplicate_field_events_do_not_duplicate_truth():
    baseline = _trace()
    field = (*baseline[:3], baseline[2], *baseline[3:], baseline[4])
    result = replay_field_trace(baseline, field)

    assert result.verified is True
    assert len(result.field_authoritative_trace) == len(baseline)


def _trace() -> tuple[dict[str, object], ...]:
    return tuple(_event(index) for index in range(7))


def _event(index: int) -> dict[str, object]:
    identity = "rider.field.001" if index < 3 else "driver.field.001"
    actions = (
        "request",
        "match",
        "price_quote",
        "accept",
        "pickup",
        "dropoff",
        "complete",
    )
    payload: dict[str, object] = {
        "action": actions[index],
        "ride_id": "ride.field.001",
    }
    if actions[index] == "match":
        payload["driver_id"] = "driver.field.001"
    if actions[index] == "price_quote":
        payload["fare_cents"] = 1900
    return {
        "event_id": f"field.event.{index:03d}",
        "identity_id": identity,
        "partition_id": f"partition.{sum(identity.encode('utf-8')) % 4}",
        "payload": payload,
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:03:{index:02d}Z",
    }


def _gps_event(index: int, latitude: float, longitude: float) -> dict[str, object]:
    return {
        "event_id": f"field.gps.{index:03d}",
        "identity_id": "driver.field.001",
        "partition_id": f"partition.{sum('driver.field.001'.encode('utf-8')) % 4}",
        "payload": {
            "action": "gps_update",
            "latitude": latitude,
            "longitude": longitude,
            "ride_id": "ride.field.001",
        },
        "received_order": index,
        "sequence": index,
        "source": "device_gps",
        "source_timestamp": f"2026-05-27T00:03:{index % 60:02d}Z",
    }

