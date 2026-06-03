from __future__ import annotations

import pytest

from afritech.afripower import constants as afripower_constants


# =============================================================================
# IDENTITY
# =============================================================================


def test_component_identity():
    assert afripower_constants.AFRIPOWER_COMPONENT == "AFRIPower"


def test_component_id():
    assert afripower_constants.AFRIPOWER_COMPONENT_ID == (
        "afritech.afripower"
    )


def test_projection_status():
    assert afripower_constants.AFRIPOWER_PROJECTION_STATUS == (
        "ENTERPRISE_INTELLIGENCE_PROJECTION"
    )


def test_intelligence_status():
    assert afripower_constants.INTELLIGENCE_STATUS == (
        "READ_ONLY_ENTERPRISE_INTELLIGENCE"
    )


# =============================================================================
# AUTHORITY BOUNDARY
# =============================================================================


def test_runtime_authority_disabled():
    assert afripower_constants.RUNTIME_AUTHORITY is False


def test_enforcement_authority_disabled():
    assert afripower_constants.ENFORCEMENT_AUTHORITY is False


def test_validation_authority_disabled():
    assert afripower_constants.VALIDATION_AUTHORITY is False


def test_replay_authority_disabled():
    assert afripower_constants.REPLAY_AUTHORITY is False


def test_proof_authority_disabled():
    assert afripower_constants.PROOF_AUTHORITY is False


def test_ci_authority_disabled():
    assert afripower_constants.CI_AUTHORITY is False


def test_governance_authority_disabled():
    assert afripower_constants.GOVERNANCE_AUTHORITY is False


def test_decision_authority_disabled():
    assert afripower_constants.DECISION_AUTHORITY is False


def test_admissibility_authority_disabled():
    assert afripower_constants.ADMISSIBILITY_AUTHORITY is False


def test_intelligence_authority_disabled():
    assert afripower_constants.INTELLIGENCE_AUTHORITY is False


def test_execution_authority_disabled():
    assert afripower_constants.EXECUTION_AUTHORITY is False


def test_authoritative_disabled():
    assert afripower_constants.AUTHORITATIVE is False


def test_projection_creates_authority_disabled():
    assert afripower_constants.PROJECTION_CREATES_AUTHORITY is False


# =============================================================================
# SAFETY FLAGS
# =============================================================================


def test_reference_only():
    assert afripower_constants.REFERENCE_ONLY is True


def test_read_only():
    assert afripower_constants.READ_ONLY is True


def test_display_only():
    assert afripower_constants.DISPLAY_ONLY is True


def test_observational_only():
    assert afripower_constants.OBSERVATIONAL_ONLY is True


def test_interpretive_only():
    assert afripower_constants.INTERPRETIVE_ONLY is True


def test_representation_only():
    assert afripower_constants.REPRESENTATION_ONLY is True


def test_projection_only():
    assert afripower_constants.PROJECTION_ONLY is True


def test_enterprise_intelligence_only():
    assert afripower_constants.ENTERPRISE_INTELLIGENCE_ONLY is True


# =============================================================================
# MUTATION PROTECTION
# =============================================================================


def test_mutation_disabled():
    assert afripower_constants.MUTATION_ALLOWED is False


def test_receipt_mutation_disabled():
    assert afripower_constants.RECEIPT_MUTATION_ALLOWED is False


def test_proof_mutation_disabled():
    assert afripower_constants.PROOF_MUTATION_ALLOWED is False


def test_governance_mutation_disabled():
    assert afripower_constants.GOVERNANCE_MUTATION_ALLOWED is False


def test_runtime_dependency_disabled():
    assert afripower_constants.RUNTIME_DEPENDENCY is False


# =============================================================================
# CONSTITUTIONAL LAW FLAGS
# =============================================================================


def test_law_read_only():
    assert afripower_constants.LAW_AFRIPOWER_IS_READ_ONLY is True


def test_law_non_authoritative():
    assert afripower_constants.LAW_AFRIPOWER_IS_NON_AUTHORITATIVE is True


def test_law_display_only():
    assert afripower_constants.LAW_AFRIPOWER_IS_DISPLAY_ONLY is True


def test_law_consumes_authority_only():
    assert afripower_constants.LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY is True


def test_law_cannot_create_authority():
    assert (
        afripower_constants.LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE
        is True
    )


def test_law_cannot_influence_runtime():
    assert afripower_constants.LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME is True


def test_law_cannot_influence_replay():
    assert afripower_constants.LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY is True


def test_law_cannot_influence_proof():
    assert afripower_constants.LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF is True


def test_law_cannot_influence_ci():
    assert afripower_constants.LAW_AFRIPOWER_CANNOT_INFLUENCE_CI is True


def test_law_cannot_influence_governance():
    assert (
        afripower_constants.LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE
        is True
    )


# =============================================================================
# NODE TYPES
# =============================================================================


def test_allowed_node_types_present():
    assert len(afripower_constants.ALLOWED_NODE_TYPES) > 0


def test_execution_node_supported():
    assert "Execution" in afripower_constants.ALLOWED_NODE_TYPES


def test_proof_node_supported():
    assert "Proof" in afripower_constants.ALLOWED_NODE_TYPES


def test_traceability_node_supported():
    assert "Traceability" in afripower_constants.ALLOWED_NODE_TYPES


# =============================================================================
# EDGE TYPES
# =============================================================================


def test_allowed_edge_types_present():
    assert len(afripower_constants.ALLOWED_EDGE_TYPES) > 0


def test_reference_edge_supported():
    assert "references" in afripower_constants.ALLOWED_EDGE_TYPES


def test_supports_edge_supported():
    assert "supports" in afripower_constants.ALLOWED_EDGE_TYPES


# =============================================================================
# METADATA CONTRACT
# =============================================================================


def test_metadata_returns_dictionary():
    metadata = (
        afripower_constants.constitutional_afripower_metadata()
    )

    assert isinstance(metadata, dict)


def test_metadata_component():
    metadata = (
        afripower_constants.constitutional_afripower_metadata()
    )

    assert metadata["component"] == "AFRIPower"


def test_metadata_read_only():
    metadata = (
        afripower_constants.constitutional_afripower_metadata()
    )

    assert metadata["read_only"] is True


def test_metadata_reference_only():
    metadata = (
        afripower_constants.constitutional_afripower_metadata()
    )

    assert metadata["reference_only"] is True


def test_metadata_non_authoritative():
    metadata = (
        afripower_constants.constitutional_afripower_metadata()
    )

    assert metadata["authoritative"] is False


def test_metadata_projection_does_not_create_authority():
    metadata = (
        afripower_constants.constitutional_afripower_metadata()
    )

    assert metadata["projection_creates_authority"] is False


# =============================================================================
# CONSTITUTIONAL ASSERTION
# =============================================================================


def test_constitution_assertion_passes():
    afripower_constants.assert_afripower_constitution()


def test_constitutional_statement_present():
    assert (
        len(afripower_constants.CONSTITUTIONAL_STATEMENT)
        > 20
    )


# =============================================================================
# FAIL-CLOSED COVERAGE
# =============================================================================


def test_metadata_contains_expected_keys():
    metadata = (
        afripower_constants.constitutional_afripower_metadata()
    )

    expected = (
        "component",
        "projection_status",
        "read_only",
        "reference_only",
        "display_only",
        "runtime_authority",
        "validation_authority",
        "governance_authority",
    )

    for key in expected:
        assert key in metadata


def test_projection_never_authoritative():
    metadata = (
        afripower_constants.constitutional_afripower_metadata()
    )

    assert metadata["runtime_authority"] is False
    assert metadata["validation_authority"] is False
    assert metadata["governance_authority"] is False
    assert metadata["authoritative"] is False
