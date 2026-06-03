from __future__ import annotations

from afritech.ci.entropy_invariants_validator import validate
from afritech.runtime.entropy import (
    DisturbanceType,
    EntropyEnvelope,
    check_admissibility,
    classify,
    converge,
    normalize,
)
from afritech.runtime.entropy.proof import (
    REQUIRED_SCENARIOS,
    run_entropy_bound_execution_proof,
)


def test_entropy_proof_preserves_core_invariants():
    report = run_entropy_bound_execution_proof()

    assert report.verified is True
    assert tuple(scenario.scenario for scenario in report.scenarios) == REQUIRED_SCENARIOS
    for scenario in report.scenarios:
        assert scenario.same_replay_hash is True
        assert scenario.same_identity_resolution is True
        assert scenario.same_admissibility_decision is True
        assert scenario.same_convergence_result is True


def test_entropy_validator_accepts_declared_scenarios():
    report = validate()

    assert report.verified is True
    assert report.scenarios == REQUIRED_SCENARIOS


def test_duplicate_messages_are_recorded_but_do_not_change_replay_truth():
    event = _event(0)
    result = converge((event, event))

    assert result.final_state["accepted_event_count"] == 1
    assert [record.classification for record in result.records] == [
        DisturbanceType.NORMAL,
        DisturbanceType.DUPLICATE,
    ]


def test_out_of_order_events_converge_to_canonical_sequence():
    events = (_event(2), _event(0), _event(1))
    result = converge(events)

    assert result.final_state["accepted_event_ids"] == [
        "entropy.test.000",
        "entropy.test.001",
        "entropy.test.002",
    ]
    assert any(
        record.classification == DisturbanceType.OUT_OF_ORDER
        for record in result.records
    )


def test_clock_drift_does_not_define_ordering_truth():
    baseline = converge(tuple(_event(index) for index in range(3)))
    drifted = converge(
        tuple(
            {
                **_event(index),
                "source_timestamp": f"drift:node-clock:{100 - index}",
            }
            for index in range(3)
        )
    )

    assert drifted.replay_hash == baseline.replay_hash
    assert drifted.identity_resolution_hash == baseline.identity_resolution_hash


def test_partial_corruption_is_rejected_and_isolated():
    corrupted = normalize(
        {
            **_event(0),
            "payload": "provider-fragment",
            "corrupted": True,
        }
    )
    decision = check_admissibility(corrupted)

    assert classify(corrupted) == DisturbanceType.CORRUPTED
    assert decision.admitted is False
    assert decision.reason == "payload_not_mapping"


def test_envelope_records_entropy_evidence_without_granting_authority():
    envelope = EntropyEnvelope()
    first = envelope.ingest(_event(0))
    duplicate = envelope.ingest(_event(0))

    assert first.admissibility.admitted is True
    assert duplicate.classification == DisturbanceType.DUPLICATE
    assert len(first.replay_hash) == 64
    assert len(duplicate.replay_hash) == 64


def _event(index: int) -> dict[str, object]:
    identity = "rider.entropy.test"
    return {
        "event_id": f"entropy.test.{index:03d}",
        "identity_id": identity,
        "partition_id": f"partition.{sum(identity.encode('utf-8')) % 4}",
        "payload": {
            "action": f"step.{index}",
            "ride_id": "ride.entropy.test",
        },
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-26T00:00:{index:02d}Z",
    }
