from __future__ import annotations

import pytest

from afritech.ci.security_adversarial_validator import (
    run_security_adversarial_validation,
)
from afritech.security.adversarial_proof import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_ATTACKS,
    SecurityAdversarialProofError,
    _expect_rejection,
    run_security_adversarial_proof,
)


def test_security_adversarial_proof_covers_required_attacks():
    report = run_security_adversarial_proof()

    assert tuple(evidence.attack_name for evidence in report.attacks) == REQUIRED_ATTACKS
    assert report.verified is True
    assert report.authority_disclaimer == AUTHORITY_DISCLAIMER


def test_security_adversarial_proof_preserves_baseline_replay_hash():
    report = run_security_adversarial_proof()

    assert all(
        evidence.observed_replay_hash == report.baseline_replay_hash
        for evidence in report.attacks
    )
    assert len(report.baseline_replay_hash) == 64


def test_security_adversarial_proof_rejects_every_hostile_surface():
    report = run_security_adversarial_proof()

    assert all(evidence.disposition == "rejected" for evidence in report.attacks)
    assert all(evidence.truth_authority == "replay_validation" for evidence in report.attacks)


def test_security_adversarial_proof_hash_is_deterministic():
    first = run_security_adversarial_proof()
    second = run_security_adversarial_proof()

    assert first.report_hash() == second.report_hash()
    assert len(first.report_hash()) == 64


def test_security_adversarial_harness_fails_if_attack_is_admitted():
    with pytest.raises(SecurityAdversarialProofError, match="attack admitted"):
        _expect_rejection(
            attack_name="fake_replay_hash",
            hostile_surface="test",
            reason="admitted test attack",
            baseline_replay_hash="0" * 64,
            attempt=lambda: None,
        )


def test_security_adversarial_validator_report_is_verified():
    report = run_security_adversarial_validation()

    assert report.verified is True
    assert report.attack_count == len(REQUIRED_ATTACKS)
    assert report.rejected_attacks == REQUIRED_ATTACKS
    assert len(report.report_hash()) == 64

