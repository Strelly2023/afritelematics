"""
Constitutional constants for AFRIPower graph projection.

AFRIPower graph projection is an enterprise intelligence projection layer.

─────────────────────────────────────────────────────────────────────
CONSTITUTIONAL LAW
─────────────────────────────────────────────────────────────────────

AFRIPower consumes authority.
AFRIPower does not create authority.

AFRIPower observes.
AFRIPower does not govern.

AFRIPower explains.
AFRIPower does not validate.

AFRIPower analyzes.
AFRIPower does not execute.

─────────────────────────────────────────────────────────────────────
BOUNDARY GUARANTEES
─────────────────────────────────────────────────────────────────────

AFRIPower MUST NOT:
    - execute runtime behavior
    - validate runtime truth
    - enforce governance
    - mutate receipts
    - mutate proof artifacts
    - create replay authority
    - create proof authority
    - create CI authority
    - create governance authority
"""

from __future__ import annotations
from typing import Dict, Tuple

# ---------------------------------------------------------------------
# Component Identity
# ---------------------------------------------------------------------

AFRIPOWER_COMPONENT = "AFRIPOWER_GRAPH_PROJECTION"
AFRIPOWER_PROJECTION_STATUS = "ENTERPRISE_INTELLIGENCE_PROJECTION"
AFRIPOWER_VERSION = "1.0"

# ---------------------------------------------------------------------
# Authority Boundaries (ALL MUST REMAIN FALSE)
# ---------------------------------------------------------------------

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

# ---------------------------------------------------------------------
# Projection Boundaries (ALL TRUE = SAFE FLAGS)
# ---------------------------------------------------------------------

REFERENCE_ONLY: bool = True
READ_ONLY: bool = True
DISPLAY_ONLY: bool = True
OBSERVATIONAL_ONLY: bool = True
INTERPRETIVE_ONLY: bool = True
REPRESENTATION_ONLY: bool = True
PROJECTION_ONLY: bool = True
ENTERPRISE_INTELLIGENCE_ONLY: bool = True

# ---------------------------------------------------------------------
# Mutation / Dependency Constraints
# ---------------------------------------------------------------------

MUTATION_ALLOWED: bool = False
RECEIPT_MUTATION_ALLOWED: bool = False
PROOF_MUTATION_ALLOWED: bool = False
GOVERNANCE_MUTATION_ALLOWED: bool = False
RUNTIME_DEPENDENCY: bool = False
PROJECTION_CREATES_AUTHORITY: bool = False

# ---------------------------------------------------------------------
# Projection Source Classes
# ---------------------------------------------------------------------

ALLOWED_PROJECTION_SOURCES: Tuple[str, ...] = (
    "Doctrine",
    "Governance",
    "Execution",
    "Proof",
    "Traceability",
    "Explainability",
)

# ---------------------------------------------------------------------
# Node Types (Representation Only)
# ---------------------------------------------------------------------

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

# ---------------------------------------------------------------------
# Edge Types (Non-Authoritative)
# ---------------------------------------------------------------------

ALLOWED_EDGE_TYPES: Tuple[str, ...] = (
    "projects",
    "references",
    "explains",
    "supports",
    "depends_on",
    "linked_to",
    "impacts",
)

# ---------------------------------------------------------------------
# Data Classification
# ---------------------------------------------------------------------

GRAPH_DATA_CLASSIFICATION = "REFERENCE_ONLY"
GRAPH_OUTPUT_CLASSIFICATION = "ENTERPRISE_INTELLIGENCE_VIEW"
GRAPH_RELATIONSHIP_CLASSIFICATION = "NON_AUTHORITATIVE"

# ---------------------------------------------------------------------
# Constitutional Law Assertions (TRUE = LAW, NOT AUTHORITY)
# ---------------------------------------------------------------------

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

# ---------------------------------------------------------------------
# Validator Expectations
# ---------------------------------------------------------------------

EXPECTED_VALIDATOR_NAME = "afritech.ci.afripower_intelligence_validator"
EXPECTED_TEST_MODULE = "afritech.tests.ci.test_afripower_intelligence_validator"

# ---------------------------------------------------------------------
# Constitutional Statement (Canonical)
# ---------------------------------------------------------------------

CONSTITUTIONAL_STATEMENT = (
    "AFRIPower graph projection is a read-only enterprise intelligence "
    "projection surface. It consumes doctrine, governance, execution, proof, "
    "traceability, and explainability as references for visualization and analysis. "
    "It does not create authority or influence runtime, replay, CI, proof, "
    "or governance behavior."
)
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def constitutional_afripower_metadata() -> Dict[str, object]:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_constitutional_afripower_metadata__mutmut_orig, x_constitutional_afripower_metadata__mutmut_mutants, args, kwargs, None)

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_orig() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_1() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "XXcomponentXX": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_2() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "COMPONENT": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_3() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "XXprojection_statusXX": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_4() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "PROJECTION_STATUS": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_5() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "XXversionXX": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_6() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "VERSION": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_7() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "XXruntime_authorityXX": RUNTIME_AUTHORITY,
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_8() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "RUNTIME_AUTHORITY": RUNTIME_AUTHORITY,
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_9() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "XXenforcement_authorityXX": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_10() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "ENFORCEMENT_AUTHORITY": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_11() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "XXvalidation_authorityXX": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_12() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "VALIDATION_AUTHORITY": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_13() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "XXreplay_authorityXX": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_14() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "REPLAY_AUTHORITY": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_15() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "XXproof_authorityXX": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_16() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "PROOF_AUTHORITY": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_17() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "XXci_authorityXX": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_18() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "CI_AUTHORITY": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_19() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "XXgovernance_authorityXX": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_20() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "GOVERNANCE_AUTHORITY": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_21() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "XXdecision_authorityXX": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_22() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "DECISION_AUTHORITY": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_23() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "XXadmissibility_authorityXX": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_24() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "ADMISSIBILITY_AUTHORITY": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_25() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "XXintelligence_authorityXX": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_26() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
        "runtime_authority": RUNTIME_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "validation_authority": VALIDATION_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "decision_authority": DECISION_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "INTELLIGENCE_AUTHORITY": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_27() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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
        "XXexecution_authorityXX": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_28() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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
        "EXECUTION_AUTHORITY": EXECUTION_AUTHORITY,

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_29() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "XXreference_onlyXX": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_30() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "REFERENCE_ONLY": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_31() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "XXread_onlyXX": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_32() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "READ_ONLY": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_33() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "XXdisplay_onlyXX": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_34() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "DISPLAY_ONLY": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_35() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "XXobservational_onlyXX": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_36() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "OBSERVATIONAL_ONLY": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_37() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "XXinterpretive_onlyXX": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_38() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "INTERPRETIVE_ONLY": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_39() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "XXrepresentation_onlyXX": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_40() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "REPRESENTATION_ONLY": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_41() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "XXprojection_onlyXX": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_42() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "PROJECTION_ONLY": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_43() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "XXenterprise_intelligence_onlyXX": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_44() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "ENTERPRISE_INTELLIGENCE_ONLY": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_45() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "XXmutation_allowedXX": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_46() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "MUTATION_ALLOWED": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_47() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "XXreceipt_mutation_allowedXX": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_48() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "RECEIPT_MUTATION_ALLOWED": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_49() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "XXproof_mutation_allowedXX": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_50() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "PROOF_MUTATION_ALLOWED": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_51() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "XXgovernance_mutation_allowedXX": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_52() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "GOVERNANCE_MUTATION_ALLOWED": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_53() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "XXruntime_dependencyXX": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_54() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "RUNTIME_DEPENDENCY": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_55() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "XXprojection_creates_authorityXX": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_56() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "PROJECTION_CREATES_AUTHORITY": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_57() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "XXgraph_data_classificationXX": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_58() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "GRAPH_DATA_CLASSIFICATION": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_59() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "XXgraph_output_classificationXX": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_60() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "GRAPH_OUTPUT_CLASSIFICATION": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_61() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "XXgraph_relationship_classificationXX": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_62() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "GRAPH_RELATIONSHIP_CLASSIFICATION": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_63() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "XXlaw_read_onlyXX": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_64() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "LAW_READ_ONLY": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_65() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "XXlaw_non_authoritativeXX": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_66() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "LAW_NON_AUTHORITATIVE": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_67() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "XXlaw_display_onlyXX": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_68() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "LAW_DISPLAY_ONLY": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "law_consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_69() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "XXlaw_consumes_authority_onlyXX": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

# ---------------------------------------------------------------------
# Metadata Export (Canonical)
# ---------------------------------------------------------------------


def x_constitutional_afripower_metadata__mutmut_70() -> Dict[str, object]:
    """
    Return canonical AFRIPower metadata for:
    - validators
    - checkpoints
    - CI assertions

    ❗ Pure function:
        No mutation
        No side effects
        Deterministic
    """

    return {
        "component": AFRIPOWER_COMPONENT,
        "projection_status": AFRIPOWER_PROJECTION_STATUS,
        "version": AFRIPOWER_VERSION,

        # authority layer
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

        # projection behavior
        "reference_only": REFERENCE_ONLY,
        "read_only": READ_ONLY,
        "display_only": DISPLAY_ONLY,
        "observational_only": OBSERVATIONAL_ONLY,
        "interpretive_only": INTERPRETIVE_ONLY,
        "representation_only": REPRESENTATION_ONLY,
        "projection_only": PROJECTION_ONLY,
        "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,

        # mutation safety
        "mutation_allowed": MUTATION_ALLOWED,
        "receipt_mutation_allowed": RECEIPT_MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "runtime_dependency": RUNTIME_DEPENDENCY,
        "projection_creates_authority": PROJECTION_CREATES_AUTHORITY,

        # classification
        "graph_data_classification": GRAPH_DATA_CLASSIFICATION,
        "graph_output_classification": GRAPH_OUTPUT_CLASSIFICATION,
        "graph_relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

        # law assertions
        "law_read_only": LAW_AFRIPOWER_IS_READ_ONLY,
        "law_non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
        "law_display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
        "LAW_CONSUMES_AUTHORITY_ONLY": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    }

x_constitutional_afripower_metadata__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_constitutional_afripower_metadata__mutmut_1': x_constitutional_afripower_metadata__mutmut_1, 
    'x_constitutional_afripower_metadata__mutmut_2': x_constitutional_afripower_metadata__mutmut_2, 
    'x_constitutional_afripower_metadata__mutmut_3': x_constitutional_afripower_metadata__mutmut_3, 
    'x_constitutional_afripower_metadata__mutmut_4': x_constitutional_afripower_metadata__mutmut_4, 
    'x_constitutional_afripower_metadata__mutmut_5': x_constitutional_afripower_metadata__mutmut_5, 
    'x_constitutional_afripower_metadata__mutmut_6': x_constitutional_afripower_metadata__mutmut_6, 
    'x_constitutional_afripower_metadata__mutmut_7': x_constitutional_afripower_metadata__mutmut_7, 
    'x_constitutional_afripower_metadata__mutmut_8': x_constitutional_afripower_metadata__mutmut_8, 
    'x_constitutional_afripower_metadata__mutmut_9': x_constitutional_afripower_metadata__mutmut_9, 
    'x_constitutional_afripower_metadata__mutmut_10': x_constitutional_afripower_metadata__mutmut_10, 
    'x_constitutional_afripower_metadata__mutmut_11': x_constitutional_afripower_metadata__mutmut_11, 
    'x_constitutional_afripower_metadata__mutmut_12': x_constitutional_afripower_metadata__mutmut_12, 
    'x_constitutional_afripower_metadata__mutmut_13': x_constitutional_afripower_metadata__mutmut_13, 
    'x_constitutional_afripower_metadata__mutmut_14': x_constitutional_afripower_metadata__mutmut_14, 
    'x_constitutional_afripower_metadata__mutmut_15': x_constitutional_afripower_metadata__mutmut_15, 
    'x_constitutional_afripower_metadata__mutmut_16': x_constitutional_afripower_metadata__mutmut_16, 
    'x_constitutional_afripower_metadata__mutmut_17': x_constitutional_afripower_metadata__mutmut_17, 
    'x_constitutional_afripower_metadata__mutmut_18': x_constitutional_afripower_metadata__mutmut_18, 
    'x_constitutional_afripower_metadata__mutmut_19': x_constitutional_afripower_metadata__mutmut_19, 
    'x_constitutional_afripower_metadata__mutmut_20': x_constitutional_afripower_metadata__mutmut_20, 
    'x_constitutional_afripower_metadata__mutmut_21': x_constitutional_afripower_metadata__mutmut_21, 
    'x_constitutional_afripower_metadata__mutmut_22': x_constitutional_afripower_metadata__mutmut_22, 
    'x_constitutional_afripower_metadata__mutmut_23': x_constitutional_afripower_metadata__mutmut_23, 
    'x_constitutional_afripower_metadata__mutmut_24': x_constitutional_afripower_metadata__mutmut_24, 
    'x_constitutional_afripower_metadata__mutmut_25': x_constitutional_afripower_metadata__mutmut_25, 
    'x_constitutional_afripower_metadata__mutmut_26': x_constitutional_afripower_metadata__mutmut_26, 
    'x_constitutional_afripower_metadata__mutmut_27': x_constitutional_afripower_metadata__mutmut_27, 
    'x_constitutional_afripower_metadata__mutmut_28': x_constitutional_afripower_metadata__mutmut_28, 
    'x_constitutional_afripower_metadata__mutmut_29': x_constitutional_afripower_metadata__mutmut_29, 
    'x_constitutional_afripower_metadata__mutmut_30': x_constitutional_afripower_metadata__mutmut_30, 
    'x_constitutional_afripower_metadata__mutmut_31': x_constitutional_afripower_metadata__mutmut_31, 
    'x_constitutional_afripower_metadata__mutmut_32': x_constitutional_afripower_metadata__mutmut_32, 
    'x_constitutional_afripower_metadata__mutmut_33': x_constitutional_afripower_metadata__mutmut_33, 
    'x_constitutional_afripower_metadata__mutmut_34': x_constitutional_afripower_metadata__mutmut_34, 
    'x_constitutional_afripower_metadata__mutmut_35': x_constitutional_afripower_metadata__mutmut_35, 
    'x_constitutional_afripower_metadata__mutmut_36': x_constitutional_afripower_metadata__mutmut_36, 
    'x_constitutional_afripower_metadata__mutmut_37': x_constitutional_afripower_metadata__mutmut_37, 
    'x_constitutional_afripower_metadata__mutmut_38': x_constitutional_afripower_metadata__mutmut_38, 
    'x_constitutional_afripower_metadata__mutmut_39': x_constitutional_afripower_metadata__mutmut_39, 
    'x_constitutional_afripower_metadata__mutmut_40': x_constitutional_afripower_metadata__mutmut_40, 
    'x_constitutional_afripower_metadata__mutmut_41': x_constitutional_afripower_metadata__mutmut_41, 
    'x_constitutional_afripower_metadata__mutmut_42': x_constitutional_afripower_metadata__mutmut_42, 
    'x_constitutional_afripower_metadata__mutmut_43': x_constitutional_afripower_metadata__mutmut_43, 
    'x_constitutional_afripower_metadata__mutmut_44': x_constitutional_afripower_metadata__mutmut_44, 
    'x_constitutional_afripower_metadata__mutmut_45': x_constitutional_afripower_metadata__mutmut_45, 
    'x_constitutional_afripower_metadata__mutmut_46': x_constitutional_afripower_metadata__mutmut_46, 
    'x_constitutional_afripower_metadata__mutmut_47': x_constitutional_afripower_metadata__mutmut_47, 
    'x_constitutional_afripower_metadata__mutmut_48': x_constitutional_afripower_metadata__mutmut_48, 
    'x_constitutional_afripower_metadata__mutmut_49': x_constitutional_afripower_metadata__mutmut_49, 
    'x_constitutional_afripower_metadata__mutmut_50': x_constitutional_afripower_metadata__mutmut_50, 
    'x_constitutional_afripower_metadata__mutmut_51': x_constitutional_afripower_metadata__mutmut_51, 
    'x_constitutional_afripower_metadata__mutmut_52': x_constitutional_afripower_metadata__mutmut_52, 
    'x_constitutional_afripower_metadata__mutmut_53': x_constitutional_afripower_metadata__mutmut_53, 
    'x_constitutional_afripower_metadata__mutmut_54': x_constitutional_afripower_metadata__mutmut_54, 
    'x_constitutional_afripower_metadata__mutmut_55': x_constitutional_afripower_metadata__mutmut_55, 
    'x_constitutional_afripower_metadata__mutmut_56': x_constitutional_afripower_metadata__mutmut_56, 
    'x_constitutional_afripower_metadata__mutmut_57': x_constitutional_afripower_metadata__mutmut_57, 
    'x_constitutional_afripower_metadata__mutmut_58': x_constitutional_afripower_metadata__mutmut_58, 
    'x_constitutional_afripower_metadata__mutmut_59': x_constitutional_afripower_metadata__mutmut_59, 
    'x_constitutional_afripower_metadata__mutmut_60': x_constitutional_afripower_metadata__mutmut_60, 
    'x_constitutional_afripower_metadata__mutmut_61': x_constitutional_afripower_metadata__mutmut_61, 
    'x_constitutional_afripower_metadata__mutmut_62': x_constitutional_afripower_metadata__mutmut_62, 
    'x_constitutional_afripower_metadata__mutmut_63': x_constitutional_afripower_metadata__mutmut_63, 
    'x_constitutional_afripower_metadata__mutmut_64': x_constitutional_afripower_metadata__mutmut_64, 
    'x_constitutional_afripower_metadata__mutmut_65': x_constitutional_afripower_metadata__mutmut_65, 
    'x_constitutional_afripower_metadata__mutmut_66': x_constitutional_afripower_metadata__mutmut_66, 
    'x_constitutional_afripower_metadata__mutmut_67': x_constitutional_afripower_metadata__mutmut_67, 
    'x_constitutional_afripower_metadata__mutmut_68': x_constitutional_afripower_metadata__mutmut_68, 
    'x_constitutional_afripower_metadata__mutmut_69': x_constitutional_afripower_metadata__mutmut_69, 
    'x_constitutional_afripower_metadata__mutmut_70': x_constitutional_afripower_metadata__mutmut_70
}
x_constitutional_afripower_metadata__mutmut_orig.__name__ = 'x_constitutional_afripower_metadata'


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def assert_afripower_constitution() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_assert_afripower_constitution__mutmut_orig, x_assert_afripower_constitution__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_orig() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_1() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = None

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_2() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(None):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_3() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError(None)

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_4() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("XXAFRIPower authority violation detectedXX")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_5() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("afripower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_6() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPOWER AUTHORITY VIOLATION DETECTED")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_7() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = None

    if not all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_8() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if all(safety_flags):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_9() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(None):
        raise RuntimeError("AFRIPower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_10() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError(None)


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_11() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("XXAFRIPower projection safety violationXX")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_12() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("afripower projection safety violation")


# ---------------------------------------------------------------------
# Integrity Helper (Used by Validators Only)
# ---------------------------------------------------------------------


def x_assert_afripower_constitution__mutmut_13() -> None:
    """
    Optional integrity assertion for CI use.

    Ensures:
        ALL authority flags are False
        ALL safety flags are True
    """

    authority_flags = [
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
    ]

    if any(authority_flags):
        raise RuntimeError("AFRIPower authority violation detected")

    safety_flags = [
        REFERENCE_ONLY,
        READ_ONLY,
        REPRESENTATION_ONLY,
        PROJECTION_ONLY,
    ]

    if not all(safety_flags):
        raise RuntimeError("AFRIPOWER PROJECTION SAFETY VIOLATION")

x_assert_afripower_constitution__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_assert_afripower_constitution__mutmut_1': x_assert_afripower_constitution__mutmut_1, 
    'x_assert_afripower_constitution__mutmut_2': x_assert_afripower_constitution__mutmut_2, 
    'x_assert_afripower_constitution__mutmut_3': x_assert_afripower_constitution__mutmut_3, 
    'x_assert_afripower_constitution__mutmut_4': x_assert_afripower_constitution__mutmut_4, 
    'x_assert_afripower_constitution__mutmut_5': x_assert_afripower_constitution__mutmut_5, 
    'x_assert_afripower_constitution__mutmut_6': x_assert_afripower_constitution__mutmut_6, 
    'x_assert_afripower_constitution__mutmut_7': x_assert_afripower_constitution__mutmut_7, 
    'x_assert_afripower_constitution__mutmut_8': x_assert_afripower_constitution__mutmut_8, 
    'x_assert_afripower_constitution__mutmut_9': x_assert_afripower_constitution__mutmut_9, 
    'x_assert_afripower_constitution__mutmut_10': x_assert_afripower_constitution__mutmut_10, 
    'x_assert_afripower_constitution__mutmut_11': x_assert_afripower_constitution__mutmut_11, 
    'x_assert_afripower_constitution__mutmut_12': x_assert_afripower_constitution__mutmut_12, 
    'x_assert_afripower_constitution__mutmut_13': x_assert_afripower_constitution__mutmut_13
}
x_assert_afripower_constitution__mutmut_orig.__name__ = 'x_assert_afripower_constitution'


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    "AFRIPOWER_COMPONENT",
    "AFRIPOWER_PROJECTION_STATUS",
    "AFRIPOWER_VERSION",
    "RUNTIME_AUTHORITY",
    "ENFORCEMENT_AUTHORITY",
    "VALIDATION_AUTHORITY",
    "REPLAY_AUTHORITY",
    "PROOF_AUTHORITY",
    "CI_AUTHORITY",
    "GOVERNANCE_AUTHORITY",
    "REFERENCE_ONLY",
    "READ_ONLY",
    "DISPLAY_ONLY",
    "OBSERVATIONAL_ONLY",
    "INTERPRETIVE_ONLY",
    "REPRESENTATION_ONLY",
    "PROJECTION_ONLY",
    "ENTERPRISE_INTELLIGENCE_ONLY",
    "ALLOWED_NODE_TYPES",
    "ALLOWED_EDGE_TYPES",
    "constitutional_afripower_metadata",
    "assert_afripower_constitution",
]