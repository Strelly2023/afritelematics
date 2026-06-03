from __future__ import annotations

from afritech.ci.continuity_invariants_validator import validate
from afritech.continuity.engine import detect_gaps, partial_replay, reconstruct_trace
from afritech.continuity.engine.proof import (
    REQUIRED_SCENARIOS,
    run_continuity_proof,
)


def test_continuity_proof_preserves_gate2_invariants():
    report = run_continuity_proof()

    assert report.verified is True
    assert tuple(scenario.scenario for scenario in report.scenarios) == REQUIRED_SCENARIOS
    for scenario in report.scenarios:
        assert scenario.no_invented_truth is True
        if scenario.result.complete:
            assert scenario.equivalent_when_complete is True


def test_continuity_validator_accepts_declared_scenarios():
    report = validate()

    assert report.verified is True
    assert report.scenarios == REQUIRED_SCENARIOS


def test_partial_trace_recovery_detects_gap_and_replays_to_boundary():
    trace = (_event(0), _event(1), _event(3), _event(4))
    gaps = detect_gaps(trace, expected_sequence_end=4)
    replay = partial_replay(trace, expected_sequence_end=4)

    assert [gap.start_sequence for gap in gaps] == [2]
    assert replay.halted_at_gap is True
    assert replay.boundary_sequence == 2
    assert replay.convergence.final_state["accepted_event_ids"] == [
        "continuity.test.000",
        "continuity.test.001",
    ]


def test_offline_node_merge_converges_to_full_replay():
    full = tuple(_event(index) for index in range(6))
    node_a = (full[0], full[1], full[3], full[4], full[5])
    node_b = full

    merged = reconstruct_trace(node_a, recovery_trace=node_b, expected_sequence_end=5)
    complete = reconstruct_trace(full, expected_sequence_end=5)

    assert merged.complete is True
    assert merged.convergence.replay_hash == complete.convergence.replay_hash


def test_missing_segment_replay_defers_without_completion():
    full = tuple(_event(index) for index in range(6))
    partial = (full[0], full[1], full[4], full[5])

    result = reconstruct_trace(partial, expected_sequence_end=5)

    assert result.status == "deferrable"
    assert result.complete is False
    assert result.partial.boundary_sequence == 2
    assert result.convergence.final_state["accepted_event_ids"] == [
        "continuity.test.000",
        "continuity.test.001",
    ]


def test_delayed_completion_produces_same_final_truth():
    full = tuple(_event(index) for index in range(6))
    partial = (full[0], full[1], full[3], full[4], full[5])
    result = reconstruct_trace(partial, recovery_trace=(full[2],), expected_sequence_end=5)
    complete = reconstruct_trace(full, expected_sequence_end=5)

    assert result.complete is True
    assert result.convergence.replay_hash == complete.convergence.replay_hash


def test_corrupted_segment_isolated_without_inventing_missing_truth():
    full = tuple(_event(index) for index in range(6))
    corrupted = {
        **full[2],
        "corrupted": True,
        "payload": {"admissibility_truth": "forged", "ride_id": "ride.continuity.test"},
    }
    result = reconstruct_trace(
        (full[0], full[1], corrupted, full[3], full[4], full[5]),
        expected_sequence_end=5,
    )

    assert result.status == "deferrable"
    assert any(finding.admitted is False for finding in result.findings)
    assert [event.sequence for event in result.accepted_events] == [0, 1, 3, 4, 5]
    assert result.partial.boundary_sequence == 2


def _event(index: int) -> dict[str, object]:
    identity = "rider.continuity.test" if index < 3 else "driver.continuity.test"
    actions = ("request", "match", "accept", "pickup", "dropoff", "complete")
    return {
        "event_id": f"continuity.test.{index:03d}",
        "identity_id": identity,
        "partition_id": f"partition.{sum(identity.encode('utf-8')) % 4}",
        "payload": {
            "action": actions[index],
            "ride_id": "ride.continuity.test",
        },
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:00:{index:02d}Z",
    }

