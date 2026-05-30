from __future__ import annotations

from afritech.afriprogramming.constants import (
    AFRIPROGRAMMING_COMPONENT,
    AFRIPROGRAMMING_COMPONENT_ID,
    AFRIPROGRAMMING_PILLAR,
    AFRIPROGRAMMING_STATUS,
    CANONICAL_DEFINITION,
    FEATURE_GROUPS,
    OUTPUTS,
    QUESTION_ANSWERED,
    PURPOSE,
    assert_afriprogramming_constitution,
    constitutional_afriprogramming_metadata,
)


def test_identity_and_canonical_definition():
    assert AFRIPROGRAMMING_COMPONENT == "AfriProgramming"
    assert AFRIPROGRAMMING_COMPONENT_ID == "afritech.afriprogramming"
    assert AFRIPROGRAMMING_PILLAR == "ENGINEERING"
    assert AFRIPROGRAMMING_STATUS == "GA_ELITE_AUTONOMOUS_ENGINEERING_PLATFORM"
    assert QUESTION_ANSWERED == "How do we build it?"
    assert PURPOSE == "Builds and verifies software systems."
    assert CANONICAL_DEFINITION.startswith(
        "AfriProgramming is a proof-aware autonomous engineering platform"
    )


def test_ga_elite_feature_groups_are_complete():
    assert len(FEATURE_GROUPS) == 17
    assert "Autonomous Engineering Agent" in FEATURE_GROUPS
    assert "Multi-Agent Engineering" in FEATURE_GROUPS
    assert "Codebase Intelligence" in FEATURE_GROUPS
    assert "AfriTech Ecosystem Integration" in FEATURE_GROUPS


def test_outputs_match_engineering_pillar():
    assert OUTPUTS == (
        "Code",
        "Tests",
        "Validators",
        "Runtime Systems",
        "Proof Artifacts",
        "Software Platforms",
    )


def test_constitutional_metadata_preserves_boundaries():
    assert_afriprogramming_constitution()
    metadata = constitutional_afriprogramming_metadata()

    assert metadata["component"] == "AfriProgramming"
    assert metadata["pillar"] == "ENGINEERING"
    assert metadata["engineering_pillar"] is True
    assert metadata["proof_aware_engineering"] is True
    assert metadata["governance_authority"] is False
    assert metadata["proof_authority"] is False
    assert metadata["replay_authority"] is False
    assert metadata["ci_authority"] is False
    assert metadata["mutation_allowed"] is False
