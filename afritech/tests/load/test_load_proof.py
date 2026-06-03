from __future__ import annotations

import pytest

from afritech.ci.load_proof_validator import _validate_report
from afritech.load.proof import LoadProofError, run_load_profile, run_required_load_proofs


def test_load_profile_preserves_replay_hash_partition_order_and_worker_result():
    profile = run_load_profile(1_000)

    assert profile.verified is True
    assert profile.replay_hash_stable is True
    assert profile.partition_order_stable is True
    assert profile.worker_result_stable is True
    assert profile.hidden_mutation_absent is True


def test_load_profile_rejects_invalid_event_count():
    with pytest.raises(LoadProofError, match="event_count"):
        run_load_profile(0)


def test_load_report_supports_declared_profiles():
    report = run_required_load_proofs((32, 128))

    assert report.verified is True
    assert [profile.event_count for profile in report.profiles] == [32, 128]
    assert len(report.report_hash()) == 64


def test_load_validator_rejects_missing_required_profile():
    report = run_required_load_proofs((1_000,))

    with pytest.raises(Exception, match="load profiles mismatch"):
        _validate_report(report)
