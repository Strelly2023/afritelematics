from __future__ import annotations

import pytest

from afritech.platform_contracts.runtime import (
    TrustLevel,
    VersionVector,
    assess_trust_level,
    validate_capability_dependencies,
)


def test_trust_level_requires_contiguous_proof() -> None:
    assessment = assess_trust_level(
        authenticated=True,
        policy_verified=True,
        evidence_produced=False,
        replay_verified=True,
    )

    assert assessment.level is TrustLevel.POLICY_VERIFIED
    assert assessment.checks == ("authenticated", "policy_verified")


def test_version_vector_rejects_non_semantic_versions() -> None:
    with pytest.raises(ValueError, match="api_version_must_be_semver"):
        VersionVector(
            platform="2.0.0",
            contract="2.0.0",
            schema="1.0.0",
            api="v1",
            replay="1.0.0",
            evidence="1.0.0",
            signature="1.0.0",
        )


def test_capability_dependencies_cannot_point_upward() -> None:
    with pytest.raises(ValueError, match="upward_capability_dependency"):
        validate_capability_dependencies(
            (
                {"id": "identity", "layer": 1, "depends_on": ["products"]},
                {"id": "products", "layer": 7, "depends_on": []},
            )
        )
