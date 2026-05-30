"""
Constitutional constants for AFRIPower.

AFRIPower is a read-only enterprise intelligence projection layer.

Constitutional law:
- AFRIPower consumes authority.
- AFRIPower does not create authority.
- AFRIPower observes.
- AFRIPower does not govern.
- AFRIPower explains.
- AFRIPower does not validate.
- AFRIPower analyzes.
- AFRIPower does not execute.
"""

from __future__ import annotations

from typing import Dict, Tuple

# =============================================================================
# COMPONENT IDENTITY
# =============================================================================

AFRIPOWER_COMPONENT = "AFRIPower"
AFRIPOWER_COMPONENT_ID = "afritech.afripower"
AFRIPOWER_PROJECTION_STATUS = "ENTERPRISE_INTELLIGENCE_PROJECTION"
AFRIPOWER_VERSION = "1.0"

# Compatibility aliases expected by tests/validators
INTELLIGENCE_STATUS = "READ_ONLY_ENTERPRISE_INTELLIGENCE"
PROJECTION_STATUS = AFRIPOWER_PROJECTION_STATUS

# =============================================================================
# AUTHORITY FLAGS — ALL MUST REMAIN FALSE
# =============================================================================

RUNTIME_AUTHORITY: bool = False
ENFORCEMENT_AUTHORITY: bool = False
VALIDATION_AUTHORITY: bool = False
REPLAY_AUTHORITY: bool = False
PROOF_AUTHORITY: bool = False
CI_AUTHORITY: bool = False
GOVERNANCE_AUTHORITY: bool = False
DECISION_AUTHORITY: bool = False
ADMISSIBILITY_AUTHORITY: bool = False
INTELLIGENCE_AUTHORITY: bool = False
EXECUTION_AUTHORITY: bool = False
AUTHORITATIVE: bool = False
PROJECTION_CREATES_AUTHORITY: bool = False

# =============================================================================
# SAFE PROJECTION FLAGS — ALL MUST REMAIN TRUE
# =============================================================================

REFERENCE_ONLY: bool = True
READ_ONLY: bool = True
DISPLAY_ONLY: bool = True
OBSERVATIONAL_ONLY: bool = True
INTERPRETIVE_ONLY: bool = True
REPRESENTATION_ONLY: bool = True
PROJECTION_ONLY: bool = True
ENTERPRISE_INTELLIGENCE_ONLY: bool = True

# =============================================================================
# MUTATION FLAGS — ALL MUST REMAIN FALSE
# =============================================================================

MUTATION_ALLOWED: bool = False
RECEIPT_MUTATION_ALLOWED: bool = False
PROOF_MUTATION_ALLOWED: bool = False
GOVERNANCE_MUTATION_ALLOWED: bool = False
RUNTIME_DEPENDENCY: bool = False

# =============================================================================
# CLASSIFICATION
# =============================================================================

GRAPH_DATA_CLASSIFICATION = "REFERENCE_ONLY"
GRAPH_OUTPUT_CLASSIFICATION = "ENTERPRISE_INTELLIGENCE_VIEW"
GRAPH_RELATIONSHIP_CLASSIFICATION = "NON_AUTHORITATIVE"
INTELLIGENCE_CLASSIFICATION = "OBSERVATIONAL_ONLY"
OUTPUT_CLASSIFICATION = "DISPLAY_ONLY"

# =============================================================================
# ALLOWED GRAPH PROJECTION SOURCES
# =============================================================================

ALLOWED_PROJECTION_SOURCES: Tuple[str, ...] = (
    "Doctrine",
    "Governance",
    "Execution",
    "Proof",
    "Traceability",
    "Explainability",
)

ALLOWED_NODE_TYPES: Tuple[str, ...] = (
    "Enterprise",
    "Capability",
    "Workflow",
    "Execution",
    "ADR",
    "Invariant",
    "Rule",
    "Binding",
    "Receipt",
    "Proof",
    "Traceability",
    "Explanation",
)

ALLOWED_EDGE_TYPES: Tuple[str, ...] = (
    "projects",
    "references",
    "explains",
    "supports",
    "depends_on",
    "linked_to",
    "impacts",
)

# =============================================================================
# CONSTITUTIONAL LAWS — TRUE MEANS LAW ASSERTION, NOT AUTHORITY
# =============================================================================

LAW_AFRIPOWER_IS_READ_ONLY = True
LAW_AFRIPOWER_IS_NON_AUTHORITATIVE = True
LAW_AFRIPOWER_IS_DISPLAY_ONLY = True
LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY = True

LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE = True
LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME = True
LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY = True
LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF = True
LAW_AFRIPOWER_CANNOT_INFLUENCE_CI = True
LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE = True

INVARIANT_AFRIPOWER_IS_READ_ONLY = LAW_AFRIPOWER_IS_READ_ONLY
INVARIANT_AFRIPOWER_IS_NON_AUTHORITATIVE = LAW_AFRIPOWER_IS_NON_AUTHORITATIVE
INVARIANT_AFRIPOWER_IS_DISPLAY_ONLY = LAW_AFRIPOWER_IS_DISPLAY_ONLY
INVARIANT_AFRIPOWER_CONSUMES_AUTHORITY_ONLY = (
    LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY
)
INVARIANT_AFRIPOWER_CANNOT_CREATE_AUTHORITY = (
    LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE
)
INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME = (
    LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME
)
INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_REPLAY = (
    LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY
)
INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_PROOF = (
    LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF
)
INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_CI = (
    LAW_AFRIPOWER_CANNOT_INFLUENCE_CI
)
INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE = (
    LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE
)

EXPECTED_VALIDATOR_NAME = "afritech.ci.afripower_intelligence_validator"
EXPECTED_TEST_MODULE = "afritech.tests.ci.test_afripower_intelligence_validator"

CONSTITUTIONAL_STATEMENT = (
    "AFRIPower is a read-only enterprise intelligence projection surface. "
    "It consumes doctrine, governance, execution, proof, traceability, and "
    "explainability as references for visualization and analysis. It does "
    "not create authority or influence runtime, replay, CI, proof, or "
    "governance behavior."
)


def constitutional_afripower_metadata() -> Dict[str, object]:
    """Return deterministic AFRIPower constitutional metadata."""

    return {
        "component": AFRIPOWER_COMPONENT,
        "component_id": AFRIPOWER_COMPONENT_ID,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "intelligence_status": INTELLIGENCE_STATUS,
        "version": AFRIPOWER_VERSION,

        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "authoritative": AUTHORITATIVE,

        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
        "intelligence_classification": INTELLIGENCE_CLASSIFICATION,
        "output_classification": OUTPUT_CLASSIFICATION,

        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
        "law_cannot_create_authority_surface": (
            LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE
        ),
        "law_cannot_influence_runtime": LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
        "law_cannot_influence_replay": LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
        "law_cannot_influence_proof": LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
        "law_cannot_influence_ci": LAW_AFRIPOWER_CANNOT_INFLUENCE_CI,
        "law_cannot_influence_governance": (
            LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE
        ),

        "constitutional_statement": CONSTITUTIONAL_STATEMENT,
    }


def assert_afripower_constitution() -> None:
    """Fail closed if AFRIPower authority boundaries are violated."""

    authority_flags = (
        RUNTIME_AUTHORITY,
        ENFORCEMENT_AUTHORITY,
        VALIDATION_AUTHORITY,
        REPLAY_AUTHORITY,
        PROOF_AUTHORITY,
        CI_AUTHORITY,
        GOVERNANCE_AUTHORITY,
        DECISION_AUTHORITY,
        ADMISSIBILITY_AUTHORITY,
        INTELLIGENCE_AUTHORITY,
        EXECUTION_AUTHORITY,
        AUTHORITATIVE,
        PROJECTION_CREATES_AUTHORITY,
    )

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    required_safety_flags = (
        REFERENCE_ONLY,
        READ_ONLY,
        DISPLAY_ONLY,
        OBSERVATIONAL_ONLY,
        INTERPRETIVE_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
        ENTERPRISE_INTELLIGENCE_ONLY,
    )

    if not all(required_safety_flags):
        raise RuntimeError("AFRIPower projection safety violation detected")

    mutation_flags = (
        MUTATION_ALLOWED,
        RECEIPT_MUTATION_ALLOWED,
        PROOF_MUTATION_ALLOWED,
        GOVERNANCE_MUTATION_ALLOWED,
        RUNTIME_DEPENDENCY,
    )

    if any(mutation_flags):
        raise RuntimeError("AFRIPower mutation violation detected")


__all__ = [
    "AFRIPOWER_COMPONENT",
    "AFRIPOWER_COMPONENT_ID",
    "AFRIPOWER_PROJECTION_STATUS",
    "AFRIPOWER_VERSION",
    "INTELLIGENCE_STATUS",
    "PROJECTION_STATUS",
    "RUNTIME_AUTHORITY",
    "ENFORCEMENT_AUTHORITY",
    "VALIDATION_AUTHORITY",
    "REPLAY_AUTHORITY",
    "PROOF_AUTHORITY",
    "CI_AUTHORITY",
    "GOVERNANCE_AUTHORITY",
    "DECISION_AUTHORITY",
    "ADMISSIBILITY_AUTHORITY",
    "INTELLIGENCE_AUTHORITY",
    "EXECUTION_AUTHORITY",
    "AUTHORITATIVE",
    "PROJECTION_CREATES_AUTHORITY",
    "REFERENCE_ONLY",
    "READ_ONLY",
    "DISPLAY_ONLY",
    "OBSERVATIONAL_ONLY",
    "INTERPRETIVE_ONLY",
    "REPRESENTATION_ONLY",
    "PROJECTION_ONLY",
    "ENTERPRISE_INTELLIGENCE_ONLY",
    "MUTATION_ALLOWED",
    "RECEIPT_MUTATION_ALLOWED",
    "PROOF_MUTATION_ALLOWED",
    "GOVERNANCE_MUTATION_ALLOWED",
    "RUNTIME_DEPENDENCY",
    "GRAPH_DATA_CLASSIFICATION",
    "GRAPH_OUTPUT_CLASSIFICATION",
    "GRAPH_RELATIONSHIP_CLASSIFICATION",
    "INTELLIGENCE_CLASSIFICATION",
    "OUTPUT_CLASSIFICATION",
    "ALLOWED_PROJECTION_SOURCES",
    "ALLOWED_NODE_TYPES",
    "ALLOWED_EDGE_TYPES",
    "LAW_AFRIPOWER_IS_READ_ONLY",
    "LAW_AFRIPOWER_IS_NON_AUTHORITATIVE",
    "LAW_AFRIPOWER_IS_DISPLAY_ONLY",
    "LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY",
    "LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE",
    "LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME",
    "LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY",
    "LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF",
    "LAW_AFRIPOWER_CANNOT_INFLUENCE_CI",
    "LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE",
    "INVARIANT_AFRIPOWER_IS_READ_ONLY",
    "INVARIANT_AFRIPOWER_IS_NON_AUTHORITATIVE",
    "INVARIANT_AFRIPOWER_IS_DISPLAY_ONLY",
    "INVARIANT_AFRIPOWER_CONSUMES_AUTHORITY_ONLY",
    "INVARIANT_AFRIPOWER_CANNOT_CREATE_AUTHORITY",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_REPLAY",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_PROOF",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_CI",
    "INVARIANT_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE",
    "EXPECTED_VALIDATOR_NAME",
    "EXPECTED_TEST_MODULE",
    "CONSTITUTIONAL_STATEMENT",
    "constitutional_afripower_metadata",
    "assert_afripower_constitution",
]
