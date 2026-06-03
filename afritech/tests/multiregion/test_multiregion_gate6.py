from __future__ import annotations

from afritech.ci.multiregion_validator import validate
from afritech.runtime.multiregion import (
    converge_regions,
    partition_regions,
    validate_consistency,
)
from afritech.runtime.multiregion.proof import (
    REQUIRED_SCENARIOS,
    run_multiregion_proof,
)
from afritech.runtime.multiregion.region_model import execute_regions


def test_multiregion_proof_preserves_global_truth():
    report = run_multiregion_proof()

    assert report.verified is True
    assert tuple(scenario.scenario for scenario in report.scenarios) == REQUIRED_SCENARIOS
    for scenario in report.scenarios:
        assert scenario.consistency.truth_unique is True
        assert scenario.consistency.identity_consistent is True
        assert scenario.consistency.admissibility_consistent is True
        assert scenario.consistency.convergence_consistent is True


def test_multiregion_validator_accepts_generated_reports():
    report = validate()

    assert report.verified is True
    assert report.scenarios == REQUIRED_SCENARIOS


def test_conflicting_local_orders_converge_to_single_replay_truth():
    baseline = _trace()
    views = partition_regions("conflicting_local_order", baseline)
    regions = execute_regions(views, expected_sequence_end=len(baseline) - 1)
    result = converge_regions(baseline, regions)
    consistency = validate_consistency(result)

    assert consistency.verified is True
    assert result.global_result.replay_hash == result.baseline.replay_hash


def test_full_partition_is_safe_until_global_merge():
    baseline = _trace()
    views = partition_regions("full_partition", baseline)
    regions = execute_regions(views, expected_sequence_end=len(baseline) - 1)

    assert any(region.local_result.status == "deferrable" for region in regions)

    result = converge_regions(baseline, regions)
    assert validate_consistency(result).truth_unique is True


def test_duplicate_cross_region_messages_do_not_affect_truth():
    baseline = _trace()
    views = partition_regions("duplicate_cross_region", baseline)
    regions = execute_regions(views, expected_sequence_end=len(baseline) - 1)
    result = converge_regions(baseline, regions)

    assert result.equivalent is True
    assert len(result.merged_trace) == len(baseline)


def _trace() -> tuple[dict[str, object], ...]:
    return tuple(_event(index) for index in range(7))


def _event(index: int) -> dict[str, object]:
    identity = "rider.multiregion.001" if index < 3 else "driver.multiregion.001"
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
        "ride_id": "ride.multiregion.001",
    }
    if actions[index] == "match":
        payload["driver_id"] = "driver.multiregion.001"
    if actions[index] == "price_quote":
        payload["fare_cents"] = 1700
    return {
        "event_id": f"multiregion.event.{index:03d}",
        "identity_id": identity,
        "partition_id": f"partition.{sum(identity.encode('utf-8')) % 4}",
        "payload": payload,
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:02:{index:02d}Z",
    }

