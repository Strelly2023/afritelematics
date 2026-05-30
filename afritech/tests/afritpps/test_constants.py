from __future__ import annotations

import pytest

from afritech.afritpps import constants


def test_afritpps_identity_and_question_are_canonical():
    assert constants.AFRITPPS_COMPONENT == "AfriTPPS"
    assert constants.AFRITPPS_COMPONENT_ID == "afritech.afritpps"
    assert constants.AFRITPPS_PILLAR == "EXECUTION"
    assert constants.AFRITPPS_STATUS == "GA_ELITE_EXECUTION_PILLAR"
    assert constants.PURPOSE == "Defines how work gets executed."
    assert constants.QUESTION_ANSWERED == "How should it be executed?"


def test_afritpps_outputs_match_execution_pillar():
    assert constants.OUTPUTS == (
        "Capabilities",
        "Workflows",
        "Processes",
        "Programs",
        "Operational Models",
        "Execution Metrics",
    )


def test_afritpps_boundary_flags_are_non_authoritative():
    metadata = constants.constitutional_afritpps_metadata()

    assert metadata["execution_pillar"] is True
    assert metadata["operational_capability"] is True
    assert metadata["workflow_orchestration"] is True
    assert metadata["process_execution"] is True
    assert metadata["program_execution"] is True
    assert metadata["performance_management"] is True
    assert metadata["capability_maturity"] is True

    for key in (
        "governance_authority",
        "proof_authority",
        "replay_authority",
        "ci_authority",
        "admissibility_authority",
        "intelligence_authority",
        "engineering_authority",
        "policy_authority",
        "constitutional_authority",
        "mutation_allowed",
        "proof_mutation_allowed",
        "replay_mutation_allowed",
        "governance_mutation_allowed",
        "authority_escalation_allowed",
    ):
        assert metadata[key] is False


def test_assert_afritpps_constitution_passes():
    constants.assert_afritpps_constitution()


def test_assert_afritpps_constitution_fails_closed(monkeypatch):
    monkeypatch.setattr(constants, "GOVERNANCE_AUTHORITY", True)

    with pytest.raises(RuntimeError, match="authority boundary"):
        constants.assert_afritpps_constitution()
