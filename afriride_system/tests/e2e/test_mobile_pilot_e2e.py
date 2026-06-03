from __future__ import annotations

import pytest

from ecosystems.afriride.simulation.mobile_pilot_proof import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_REJECTIONS,
    MobilePilotAdapter,
    MobilePilotProofError,
    _rider_request_envelope,
    run_mobile_pilot_e2e_proof,
)


def test_mobile_pilot_completes_replay_valid_trip_flow():
    report = run_mobile_pilot_e2e_proof()

    assert report.verified is True
    assert report.trip_replay_hash == report.replayed_trip_hash
    assert report.event_count >= 6
    assert report.authority_disclaimer == AUTHORITY_DISCLAIMER


def test_mobile_pilot_persists_event_evidence():
    report = run_mobile_pilot_e2e_proof()

    assert len(report.persistent_event_hash) == 64
    assert len(report.ride_hash) == 64
    assert len(report.assignment_hash) == 64
    assert len(report.price_hash) == 64


def test_mobile_pilot_rejects_required_client_authority_cases():
    report = run_mobile_pilot_e2e_proof()

    assert report.rejected_cases == REQUIRED_REJECTIONS


def test_mobile_adapter_rejects_client_replay_hash_authority():
    with pytest.raises(MobilePilotProofError, match="replay_hash"):
        MobilePilotAdapter().normalize(
            _rider_request_envelope(
                envelope_id="test.replay_hash",
                payload_extra={"replay_hash": "0" * 64},
            )
        )


def test_mobile_adapter_rejects_duplicate_request():
    adapter = MobilePilotAdapter()
    envelope = _rider_request_envelope(envelope_id="test.duplicate")
    adapter.normalize(envelope)

    with pytest.raises(MobilePilotProofError, match="duplicate"):
        adapter.normalize(envelope)


def test_mobile_pilot_report_hash_is_deterministic():
    first = run_mobile_pilot_e2e_proof()
    second = run_mobile_pilot_e2e_proof()

    assert first.report_hash() == second.report_hash()
