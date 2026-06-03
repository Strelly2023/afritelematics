from __future__ import annotations

from afritech.ci.replay_authority_validator import validate
from afritech.replay_authority.engine import (
    DisputeClaim,
    build_audit_packet,
    reconstruct_authority,
    resolve_dispute,
)
from afritech.replay_authority.engine.proof import (
    REQUIRED_SCENARIOS,
    run_replay_authority_proof,
)


def test_replay_authority_proof_preserves_all_scenarios():
    report = run_replay_authority_proof()

    assert report.verified is True
    assert tuple(scenario.scenario for scenario in report.scenarios) == REQUIRED_SCENARIOS
    for scenario in report.scenarios:
        assert scenario.same_replay_authority is True
        assert scenario.same_resolution is True


def test_replay_authority_validator_accepts_generated_reports():
    report = validate()

    assert report.verified is True
    assert report.scenarios == REQUIRED_SCENARIOS


def test_full_replay_trace_reconstructs_authoritative_decisions():
    reconstruction = reconstruct_authority(_trace())
    decisions = {decision.decision_id: decision for decision in reconstruction.decisions}

    assert decisions["ride.authority.test:fare_cents"].authoritative_value == 1500
    assert decisions["ride.authority.test:ride_status"].authoritative_value == "completed"
    assert len(reconstruction.replay_authority_hash) == 64


def test_conflicting_claims_resolve_against_replay_truth():
    claims = (
        DisputeClaim(
            asserted_value=1500,
            claim_id="claim.rider.fare",
            claimant_id="rider.authority.test",
            decision_id="ride.authority.test:fare_cents",
            supporting_event_ids=("authority.test.002",),
        ),
        DisputeClaim(
            asserted_value=9999,
            claim_id="claim.driver.fare",
            claimant_id="driver.authority.test",
            decision_id="ride.authority.test:fare_cents",
            supporting_event_ids=("authority.test.002",),
        ),
    )
    dispute = resolve_dispute(_trace(), claims)

    assert [resolution.admitted for resolution in dispute.resolutions] == [False, True]
    assert {
        resolution.reason for resolution in dispute.resolutions
    } == {
        "claim_conflicts_with_replay_authority",
        "claim_matches_replay_authority",
    }


def test_audit_packet_is_reproducible_under_disturbed_observation():
    claims = _claims()
    baseline = build_audit_packet(resolve_dispute(_trace(), claims))
    disturbed = build_audit_packet(resolve_dispute(_disturbed_trace(), claims))

    assert disturbed.audit_hash == baseline.audit_hash


def _claims() -> tuple[DisputeClaim, ...]:
    return (
        DisputeClaim(
            asserted_value=1500,
            claim_id="claim.rider.fare",
            claimant_id="rider.authority.test",
            decision_id="ride.authority.test:fare_cents",
            supporting_event_ids=("authority.test.002",),
        ),
    )


def _trace() -> tuple[dict[str, object], ...]:
    return tuple(_event(index) for index in range(7))


def _disturbed_trace() -> tuple[dict[str, object], ...]:
    trace = _trace()
    return (
        trace[0],
        {**trace[1], "received_order": 20, "partition_id": "partition.split.test"},
        trace[2],
        trace[2],
        trace[3],
        trace[4],
        trace[6],
        trace[5],
    )


def _event(index: int) -> dict[str, object]:
    identity = "rider.authority.test" if index < 3 else "driver.authority.test"
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
        "ride_id": "ride.authority.test",
    }
    if actions[index] == "match":
        payload["driver_id"] = "driver.authority.test"
    if actions[index] == "price_quote":
        payload["fare_cents"] = 1500
    return {
        "event_id": f"authority.test.{index:03d}",
        "identity_id": identity,
        "partition_id": f"partition.{sum(identity.encode('utf-8')) % 4}",
        "payload": payload,
        "received_order": index,
        "sequence": index,
        "source": "mobile_adapter",
        "source_timestamp": f"2026-05-27T00:01:{index:02d}Z",
    }

