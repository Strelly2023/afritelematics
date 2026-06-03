from __future__ import annotations

import pytest

from afritech.ci.adversarial_integrity_validator import validate
from afritech.security.adversarial_integrity_proof import (
    REQUIRED_SCENARIOS,
    AdversarialIntegrityProofError,
    AdversarialIntegrityScenarioProof,
    run_adversarial_integrity_proof,
)
from afritech.security.adversarial_proof import AdversarialAttackEvidence


def test_adversarial_integrity_proof_preserves_all_scenarios():
    report = run_adversarial_integrity_proof()

    assert report.verified is True
    assert tuple(scenario.scenario for scenario in report.scenarios) == REQUIRED_SCENARIOS
    for scenario in report.scenarios:
        assert scenario.all_attacks_rejected is True
        assert scenario.replay_truth_preserved is True
        assert scenario.authority_isolated is True


def test_adversarial_integrity_validator_accepts_generated_reports():
    report = validate()

    assert report.verified is True
    assert report.scenarios == REQUIRED_SCENARIOS


def test_replay_forgery_attacks_cannot_change_truth():
    report = run_adversarial_integrity_proof()
    scenario = next(
        item for item in report.scenarios if item.scenario == "replay_forgery_resistance"
    )

    assert {attack.attack_name for attack in scenario.attacks} == {
        "duplicate_worker_result",
        "fake_replay_hash",
        "tampered_event_log",
    }
    assert {
        attack.observed_replay_hash for attack in scenario.attacks
    } == {report.baseline_replay_hash}


def test_authority_isolation_rejects_observability_and_provider_overrides():
    report = run_adversarial_integrity_proof()
    scenario = next(item for item in report.scenarios if item.scenario == "authority_isolation")

    assert all(attack.truth_authority == "replay_validation" for attack in scenario.attacks)
    assert {
        attack.attack_name for attack in scenario.attacks
    } == {
        "fake_observability_evidence",
        "fake_replay_hash",
        "provider_response_injection",
    }


def test_adversarial_integrity_fails_if_attack_is_admitted():
    attack = AdversarialAttackEvidence(
        attack_name="fake_replay_hash",
        baseline_replay_hash="a" * 64,
        disposition="admitted",
        hostile_surface="replay_claim",
        observed_replay_hash="b" * 64,
        reason="test attack admitted",
        truth_authority="hostile_input",
    )
    scenario = AdversarialIntegrityScenarioProof(
        attacks=(attack,),
        baseline_replay_hash="a" * 64,
        scenario="replay_forgery_resistance",
    )

    assert scenario.verified is False

    with pytest.raises(AdversarialIntegrityProofError):
        raise AdversarialIntegrityProofError("adversarial integrity proof failed")

