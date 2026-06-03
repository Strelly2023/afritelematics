from __future__ import annotations

import pytest

from afritech.ci.observability_evidence_validator import (
    run_observability_evidence_proof,
)
from afritech.observability.evidence import (
    AUTHORITY_DISCLAIMER,
    ObservabilityEvidenceError,
    assert_action_allowed,
    build_observability_snapshot,
    required_metrics_present,
)


_SOURCE_HASHES = {
    "test_source": "0" * 64,
}


def _snapshot():
    return build_observability_snapshot(
        event_count=12,
        partition_lag={"partition.test": 0},
        worker_health={"worker.test": "HEALTHY"},
        replay_divergence_count=0,
        recovery_attempts=1,
        rejected_executions=0,
        source_hashes=_SOURCE_HASHES,
    )


def test_observability_dashboard_contains_required_production_metrics():
    payload = _snapshot().dashboard_payload()

    assert required_metrics_present(payload) is True
    assert payload["event_count"] == 12
    assert payload["partition_lag"] == {"partition.test": 0}
    assert payload["worker_health"] == {"worker.test": "HEALTHY"}
    assert payload["replay_divergence_count"] == 0
    assert payload["recovery_attempts"] == 1
    assert payload["rejected_executions"] == 0


def test_observability_snapshot_hash_is_deterministic():
    first = _snapshot()
    second = _snapshot()

    assert first.snapshot_hash() == second.snapshot_hash()
    assert len(first.snapshot_hash()) == 64


def test_observability_rejects_negative_metrics():
    with pytest.raises(ObservabilityEvidenceError, match="event_count"):
        build_observability_snapshot(
            event_count=-1,
            partition_lag={"partition.test": 0},
            worker_health={"worker.test": "HEALTHY"},
            replay_divergence_count=0,
            recovery_attempts=0,
            rejected_executions=0,
            source_hashes=_SOURCE_HASHES,
        )


def test_observability_rejects_invalid_worker_health():
    with pytest.raises(ObservabilityEvidenceError, match="worker_health"):
        build_observability_snapshot(
            event_count=1,
            partition_lag={"partition.test": 0},
            worker_health={"worker.test": "AUTHORITATIVE"},
            replay_divergence_count=0,
            recovery_attempts=0,
            rejected_executions=0,
            source_hashes=_SOURCE_HASHES,
        )


def test_observability_rejects_authority_actions():
    with pytest.raises(ObservabilityEvidenceError, match="non-authoritative"):
        assert_action_allowed("define_truth")

    assert assert_action_allowed("report_system_state") is True


def test_observability_payload_is_non_authoritative():
    payload = _snapshot().dashboard_payload()

    assert payload["authority_disclaimer"] == AUTHORITY_DISCLAIMER
    assert "truth" not in payload
    assert "admissibility_decision" not in payload


def test_observability_evidence_validator_report_is_verified():
    report = run_observability_evidence_proof()

    assert report.verified is True
    assert report.required_metrics_present is True
    assert report.forbidden_actions_rejected is True
    assert report.non_authoritative is True
    assert report.replay_divergence_count == 0
    assert len(report.report_hash()) == 64

