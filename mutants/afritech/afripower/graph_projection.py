"""
AFRIPower enterprise intelligence graph projection.

This module projects execution, governance, proof, traceability, and
explainability references into a read-only enterprise intelligence view.

Constitutional Law
------------------
AFRIPower consumes authority.
AFRIPower does not create authority.

AFRIPower may:
- organize references
- display relationships
- support enterprise intelligence views

AFRIPower must not:
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

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Dict, Tuple, List, Set

from afritech.afripower.graph.constants import (
    AFRIPOWER_PROJECTION_STATUS,
    ALLOWED_EDGE_TYPES,
    ALLOWED_NODE_TYPES,
    DISPLAY_ONLY,
    ENTERPRISE_INTELLIGENCE_ONLY,
    GOVERNANCE_AUTHORITY,
    GRAPH_DATA_CLASSIFICATION,
    GRAPH_OUTPUT_CLASSIFICATION,
    GRAPH_RELATIONSHIP_CLASSIFICATION,
    LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_CI,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
    LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    LAW_AFRIPOWER_IS_DISPLAY_ONLY,
    LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    LAW_AFRIPOWER_IS_READ_ONLY,
    PROJECTION_CREATES_AUTHORITY,
    PROJECTION_ONLY,
    READ_ONLY,
    REFERENCE_ONLY,
    RUNTIME_AUTHORITY,
    VALIDATION_AUTHORITY,
)

TRACEABILITY_FIELD = "governance_traceability"
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


# =============================================================================
# Node definition
# =============================================================================

@dataclass(frozen=True)
class AFRIPowerNode:
    """Immutable read-only AFRIPower graph node."""

    node_type: str
    node_id: str
    label: str | None = None

    def __post_init__(self) -> None:
        if self.node_type not in ALLOWED_NODE_TYPES:
            raise ValueError(f"unsupported AFRIPower node type: {self.node_type}")
        if not self.node_id:
            raise ValueError("AFRIPower node id is required")

    def canonical_dict(self) -> Dict[str, object]:
        return {
            "type": self.node_type,
            "id": self.node_id,
            "label": self.label or self.node_id,

            # Projection metadata
            "projection_status": AFRIPOWER_PROJECTION_STATUS,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,

            # Safety flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "reference_only": REFERENCE_ONLY,
            "projection_only": PROJECTION_ONLY,
            "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,
            "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,

            # Authority flags (ALL FALSE)
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
        }


# =============================================================================
# Edge definition
# =============================================================================

@dataclass(frozen=True)
class AFRIPowerEdge:
    """Immutable read-only AFRIPower graph edge."""

    source_id: str
    target_id: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("AFRIPower edge source_id is required")

        if not self.target_id:
            raise ValueError("AFRIPower edge target_id is required")

        if self.relation not in ALLOWED_EDGE_TYPES:
            raise ValueError(f"unsupported AFRIPower edge relation: {self.relation}")

    def canonical_dict(self) -> Dict[str, object]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,

            # Projection metadata
            "projection_status": AFRIPOWER_PROJECTION_STATUS,
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,

            # Safety flags
            "read_only": READ_ONLY,
            "display_only": DISPLAY_ONLY,
            "reference_only": REFERENCE_ONLY,
            "projection_only": PROJECTION_ONLY,
            "enterprise_intelligence_only": ENTERPRISE_INTELLIGENCE_ONLY,
            "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,

            # Authority flags
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,
            "creates_authority": PROJECTION_CREATES_AUTHORITY,

            # Influence flags (always False)
            "influences_runtime": not LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
            "influences_replay": not LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
            "influences_proof": not LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
            "influences_ci": not LAW_AFRIPOWER_CANNOT_INFLUENCE_CI,
            "influences_governance": not LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE,
        }


# =============================================================================
# Graph container
# =============================================================================

@dataclass(frozen=True)
class AFRIPowerKnowledgeGraph:
    """Immutable read-only AFRIPower enterprise intelligence graph."""

    nodes: Tuple[AFRIPowerNode, ...]
    edges: Tuple[AFRIPowerEdge, ...]

    def canonical_dict(self) -> Dict[str, object]:
        return {
            "projection_status": AFRIPOWER_PROJECTION_STATUS,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,

            # Laws
            "read_only": LAW_AFRIPOWER_IS_READ_ONLY,
            "display_only": LAW_AFRIPOWER_IS_DISPLAY_ONLY,
            "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
            "consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,

            "cannot_create_authority": LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE,
            "creates_authority": PROJECTION_CREATES_AUTHORITY,

            # Authority flags (strictly False)
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "governance_authority": GOVERNANCE_AUTHORITY,

            # Influence tracking (all False)
            "influences_runtime": not LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
            "influences_replay": not LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
            "influences_proof": not LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
            "influences_ci": not LAW_AFRIPOWER_CANNOT_INFLUENCE_CI,
            "influences_governance": not LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE,

            # Data
            "nodes": [n.canonical_dict() for n in self.nodes],
            "edges": [e.canonical_dict() for e in self.edges],
        }


# =============================================================================
# Helpers (pure, defensive)
# =============================================================================

def _safe_str(value: object) -> str:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__safe_str__mutmut_orig, x__safe_str__mutmut_mutants, args, kwargs, None)


# =============================================================================
# Helpers (pure, defensive)
# =============================================================================

def x__safe_str__mutmut_orig(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


# =============================================================================
# Helpers (pure, defensive)
# =============================================================================

def x__safe_str__mutmut_1(value: object) -> str:
    return value.strip() if isinstance(value, str) or value.strip() else ""


# =============================================================================
# Helpers (pure, defensive)
# =============================================================================

def x__safe_str__mutmut_2(value: object) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else "XXXX"

x__safe_str__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__safe_str__mutmut_1': x__safe_str__mutmut_1, 
    'x__safe_str__mutmut_2': x__safe_str__mutmut_2
}
x__safe_str__mutmut_orig.__name__ = 'x__safe_str'


def _normalize_node_type(value: str) -> str:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__normalize_node_type__mutmut_orig, x__normalize_node_type__mutmut_mutants, args, kwargs, None)


def x__normalize_node_type__mutmut_orig(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_1(value: str) -> str:
    mapping = None
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_2(value: str) -> str:
    mapping = {
        "XXEXECUTIONXX": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_3(value: str) -> str:
    mapping = {
        "execution": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_4(value: str) -> str:
    mapping = {
        "EXECUTION": "XXExecutionXX",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_5(value: str) -> str:
    mapping = {
        "EXECUTION": "execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_6(value: str) -> str:
    mapping = {
        "EXECUTION": "EXECUTION",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_7(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "XXADRXX": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_8(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "adr": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_9(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "XXADRXX",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_10(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "adr",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_11(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "XXINVARIANTXX": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_12(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "invariant": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_13(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "XXInvariantXX",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_14(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_15(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "INVARIANT",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_16(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "XXRULEXX": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_17(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "rule": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_18(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "XXRuleXX",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_19(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_20(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "RULE",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_21(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "XXBINDINGXX": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_22(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "binding": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_23(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "XXBindingXX",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_24(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_25(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "BINDING",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_26(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "XXRECEIPTXX": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_27(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "receipt": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_28(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "XXReceiptXX",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_29(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_30(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "RECEIPT",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_31(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "XXPROOFXX": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_32(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "proof": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_33(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "XXProofXX",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_34(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_35(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "PROOF",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_36(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "XXTRACEABILITYXX": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_37(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "traceability": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_38(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "XXTraceabilityXX",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_39(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_40(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "TRACEABILITY",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_41(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "XXEXPLANATIONXX": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_42(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "explanation": "Explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_43(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "XXExplanationXX",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_44(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "explanation",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_45(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "EXPLANATION",
    }
    return mapping.get(value.strip().upper(), value.strip())


def x__normalize_node_type__mutmut_46(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(None, value.strip())


def x__normalize_node_type__mutmut_47(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), None)


def x__normalize_node_type__mutmut_48(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip())


def x__normalize_node_type__mutmut_49(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().upper(), )


def x__normalize_node_type__mutmut_50(value: str) -> str:
    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "RULE": "Rule",
        "BINDING": "Binding",
        "RECEIPT": "Receipt",
        "PROOF": "Proof",
        "TRACEABILITY": "Traceability",
        "EXPLANATION": "Explanation",
    }
    return mapping.get(value.strip().lower(), value.strip())

x__normalize_node_type__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__normalize_node_type__mutmut_1': x__normalize_node_type__mutmut_1, 
    'x__normalize_node_type__mutmut_2': x__normalize_node_type__mutmut_2, 
    'x__normalize_node_type__mutmut_3': x__normalize_node_type__mutmut_3, 
    'x__normalize_node_type__mutmut_4': x__normalize_node_type__mutmut_4, 
    'x__normalize_node_type__mutmut_5': x__normalize_node_type__mutmut_5, 
    'x__normalize_node_type__mutmut_6': x__normalize_node_type__mutmut_6, 
    'x__normalize_node_type__mutmut_7': x__normalize_node_type__mutmut_7, 
    'x__normalize_node_type__mutmut_8': x__normalize_node_type__mutmut_8, 
    'x__normalize_node_type__mutmut_9': x__normalize_node_type__mutmut_9, 
    'x__normalize_node_type__mutmut_10': x__normalize_node_type__mutmut_10, 
    'x__normalize_node_type__mutmut_11': x__normalize_node_type__mutmut_11, 
    'x__normalize_node_type__mutmut_12': x__normalize_node_type__mutmut_12, 
    'x__normalize_node_type__mutmut_13': x__normalize_node_type__mutmut_13, 
    'x__normalize_node_type__mutmut_14': x__normalize_node_type__mutmut_14, 
    'x__normalize_node_type__mutmut_15': x__normalize_node_type__mutmut_15, 
    'x__normalize_node_type__mutmut_16': x__normalize_node_type__mutmut_16, 
    'x__normalize_node_type__mutmut_17': x__normalize_node_type__mutmut_17, 
    'x__normalize_node_type__mutmut_18': x__normalize_node_type__mutmut_18, 
    'x__normalize_node_type__mutmut_19': x__normalize_node_type__mutmut_19, 
    'x__normalize_node_type__mutmut_20': x__normalize_node_type__mutmut_20, 
    'x__normalize_node_type__mutmut_21': x__normalize_node_type__mutmut_21, 
    'x__normalize_node_type__mutmut_22': x__normalize_node_type__mutmut_22, 
    'x__normalize_node_type__mutmut_23': x__normalize_node_type__mutmut_23, 
    'x__normalize_node_type__mutmut_24': x__normalize_node_type__mutmut_24, 
    'x__normalize_node_type__mutmut_25': x__normalize_node_type__mutmut_25, 
    'x__normalize_node_type__mutmut_26': x__normalize_node_type__mutmut_26, 
    'x__normalize_node_type__mutmut_27': x__normalize_node_type__mutmut_27, 
    'x__normalize_node_type__mutmut_28': x__normalize_node_type__mutmut_28, 
    'x__normalize_node_type__mutmut_29': x__normalize_node_type__mutmut_29, 
    'x__normalize_node_type__mutmut_30': x__normalize_node_type__mutmut_30, 
    'x__normalize_node_type__mutmut_31': x__normalize_node_type__mutmut_31, 
    'x__normalize_node_type__mutmut_32': x__normalize_node_type__mutmut_32, 
    'x__normalize_node_type__mutmut_33': x__normalize_node_type__mutmut_33, 
    'x__normalize_node_type__mutmut_34': x__normalize_node_type__mutmut_34, 
    'x__normalize_node_type__mutmut_35': x__normalize_node_type__mutmut_35, 
    'x__normalize_node_type__mutmut_36': x__normalize_node_type__mutmut_36, 
    'x__normalize_node_type__mutmut_37': x__normalize_node_type__mutmut_37, 
    'x__normalize_node_type__mutmut_38': x__normalize_node_type__mutmut_38, 
    'x__normalize_node_type__mutmut_39': x__normalize_node_type__mutmut_39, 
    'x__normalize_node_type__mutmut_40': x__normalize_node_type__mutmut_40, 
    'x__normalize_node_type__mutmut_41': x__normalize_node_type__mutmut_41, 
    'x__normalize_node_type__mutmut_42': x__normalize_node_type__mutmut_42, 
    'x__normalize_node_type__mutmut_43': x__normalize_node_type__mutmut_43, 
    'x__normalize_node_type__mutmut_44': x__normalize_node_type__mutmut_44, 
    'x__normalize_node_type__mutmut_45': x__normalize_node_type__mutmut_45, 
    'x__normalize_node_type__mutmut_46': x__normalize_node_type__mutmut_46, 
    'x__normalize_node_type__mutmut_47': x__normalize_node_type__mutmut_47, 
    'x__normalize_node_type__mutmut_48': x__normalize_node_type__mutmut_48, 
    'x__normalize_node_type__mutmut_49': x__normalize_node_type__mutmut_49, 
    'x__normalize_node_type__mutmut_50': x__normalize_node_type__mutmut_50
}
x__normalize_node_type__mutmut_orig.__name__ = 'x__normalize_node_type'


def _extract_refs(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    args = [payload]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__extract_refs__mutmut_orig, x__extract_refs__mutmut_mutants, args, kwargs, None)


def x__extract_refs__mutmut_orig(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_1(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = None
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_2(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(None, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_3(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, None)
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_4(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get([])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_5(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, )
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_6(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = None

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_7(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) and isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_8(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_9(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = None
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_10(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(None)
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_11(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get(None))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_12(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("XXtypeXX"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_13(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("TYPE"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_14(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = None
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_15(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(None)
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_16(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get(None))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_17(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("XXidXX"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_18(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("ID"))
            if t and i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_19(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t or i:
                result.append({"type": t, "id": i})

    return result


def x__extract_refs__mutmut_20(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append(None)

    return result


def x__extract_refs__mutmut_21(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"XXtypeXX": t, "id": i})

    return result


def x__extract_refs__mutmut_22(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"TYPE": t, "id": i})

    return result


def x__extract_refs__mutmut_23(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "XXidXX": i})

    return result


def x__extract_refs__mutmut_24(payload: Mapping[str, object]) -> List[Dict[str, str]]:
    raw = payload.get(TRACEABILITY_FIELD, [])
    result: List[Dict[str, str]] = []

    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return result

    for item in raw:
        if isinstance(item, Mapping):
            t = _safe_str(item.get("type"))
            i = _safe_str(item.get("id"))
            if t and i:
                result.append({"type": t, "ID": i})

    return result

x__extract_refs__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__extract_refs__mutmut_1': x__extract_refs__mutmut_1, 
    'x__extract_refs__mutmut_2': x__extract_refs__mutmut_2, 
    'x__extract_refs__mutmut_3': x__extract_refs__mutmut_3, 
    'x__extract_refs__mutmut_4': x__extract_refs__mutmut_4, 
    'x__extract_refs__mutmut_5': x__extract_refs__mutmut_5, 
    'x__extract_refs__mutmut_6': x__extract_refs__mutmut_6, 
    'x__extract_refs__mutmut_7': x__extract_refs__mutmut_7, 
    'x__extract_refs__mutmut_8': x__extract_refs__mutmut_8, 
    'x__extract_refs__mutmut_9': x__extract_refs__mutmut_9, 
    'x__extract_refs__mutmut_10': x__extract_refs__mutmut_10, 
    'x__extract_refs__mutmut_11': x__extract_refs__mutmut_11, 
    'x__extract_refs__mutmut_12': x__extract_refs__mutmut_12, 
    'x__extract_refs__mutmut_13': x__extract_refs__mutmut_13, 
    'x__extract_refs__mutmut_14': x__extract_refs__mutmut_14, 
    'x__extract_refs__mutmut_15': x__extract_refs__mutmut_15, 
    'x__extract_refs__mutmut_16': x__extract_refs__mutmut_16, 
    'x__extract_refs__mutmut_17': x__extract_refs__mutmut_17, 
    'x__extract_refs__mutmut_18': x__extract_refs__mutmut_18, 
    'x__extract_refs__mutmut_19': x__extract_refs__mutmut_19, 
    'x__extract_refs__mutmut_20': x__extract_refs__mutmut_20, 
    'x__extract_refs__mutmut_21': x__extract_refs__mutmut_21, 
    'x__extract_refs__mutmut_22': x__extract_refs__mutmut_22, 
    'x__extract_refs__mutmut_23': x__extract_refs__mutmut_23, 
    'x__extract_refs__mutmut_24': x__extract_refs__mutmut_24
}
x__extract_refs__mutmut_orig.__name__ = 'x__extract_refs'


# =============================================================================
# Main builder
# =============================================================================

def build_afripower_knowledge_graph(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:
    args = [payloads]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_afripower_knowledge_graph__mutmut_orig, x_build_afripower_knowledge_graph__mutmut_mutants, args, kwargs, None)


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_orig(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_1(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = None
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_2(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = None

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_3(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = None
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_4(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = None

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_5(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = None
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_6(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(None)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_7(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = None
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_8(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_9(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(None)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_10(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(None)

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_11(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(None, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_12(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, None, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_13(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, None))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_14(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_15(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_16(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, ))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_17(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = None
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_18(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_19(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(None)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_20(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(None)

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_21(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(None, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_22(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, None, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_23(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, None))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_24(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_25(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_26(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, ))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_27(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = None
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_28(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) and "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_29(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(None) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_30(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get(None)) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_31(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("XXexecution_idXX")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_32(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("EXECUTION_ID")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_33(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "XXunknown-executionXX"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_34(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "UNKNOWN-EXECUTION"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_35(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node(None, exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_36(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", None)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_37(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node(exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_38(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", )

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_39(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("XXExecutionXX", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_40(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_41(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("EXECUTION", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_42(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(None):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_43(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = None
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_44(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["XXtypeXX"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_45(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["TYPE"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_46(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = None

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_47(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["XXidXX"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_48(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["ID"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_49(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(None, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_50(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, None)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_51(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_52(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, )
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_53(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(None, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_54(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, None, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_55(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, None)

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_56(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_57(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_58(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, )

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_59(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "XXreferencesXX")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_60(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "REFERENCES")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_61(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(None, tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_62(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), None)


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_63(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_64(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), )


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_65(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(None), tuple(edges))


# =============================================================================
# Main builder
# =============================================================================

def x_build_afripower_knowledge_graph__mutmut_66(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerKnowledgeGraph:

    nodes: List[AFRIPowerNode] = []
    edges: List[AFRIPowerEdge] = []

    seen_nodes: Set[Tuple[str, str]] = set()
    seen_edges: Set[Tuple[str, str, str]] = set()

    def add_node(t: str, i: str):
        t = _normalize_node_type(t)
        key = (t, i)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(AFRIPowerNode(t, i, i))

    def add_edge(s: str, t: str, r: str):
        key = (s, t, r)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(AFRIPowerEdge(s, t, r))

    for p in payloads:
        exec_id = _safe_str(p.get("execution_id")) or "unknown-execution"
        add_node("Execution", exec_id)

        for ref in _extract_refs(p):
            ref_type = ref["type"]
            ref_id = ref["id"]

            add_node(ref_type, ref_id)
            add_edge(exec_id, ref_id, "references")

    return AFRIPowerKnowledgeGraph(tuple(nodes), tuple(None))

x_build_afripower_knowledge_graph__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_afripower_knowledge_graph__mutmut_1': x_build_afripower_knowledge_graph__mutmut_1, 
    'x_build_afripower_knowledge_graph__mutmut_2': x_build_afripower_knowledge_graph__mutmut_2, 
    'x_build_afripower_knowledge_graph__mutmut_3': x_build_afripower_knowledge_graph__mutmut_3, 
    'x_build_afripower_knowledge_graph__mutmut_4': x_build_afripower_knowledge_graph__mutmut_4, 
    'x_build_afripower_knowledge_graph__mutmut_5': x_build_afripower_knowledge_graph__mutmut_5, 
    'x_build_afripower_knowledge_graph__mutmut_6': x_build_afripower_knowledge_graph__mutmut_6, 
    'x_build_afripower_knowledge_graph__mutmut_7': x_build_afripower_knowledge_graph__mutmut_7, 
    'x_build_afripower_knowledge_graph__mutmut_8': x_build_afripower_knowledge_graph__mutmut_8, 
    'x_build_afripower_knowledge_graph__mutmut_9': x_build_afripower_knowledge_graph__mutmut_9, 
    'x_build_afripower_knowledge_graph__mutmut_10': x_build_afripower_knowledge_graph__mutmut_10, 
    'x_build_afripower_knowledge_graph__mutmut_11': x_build_afripower_knowledge_graph__mutmut_11, 
    'x_build_afripower_knowledge_graph__mutmut_12': x_build_afripower_knowledge_graph__mutmut_12, 
    'x_build_afripower_knowledge_graph__mutmut_13': x_build_afripower_knowledge_graph__mutmut_13, 
    'x_build_afripower_knowledge_graph__mutmut_14': x_build_afripower_knowledge_graph__mutmut_14, 
    'x_build_afripower_knowledge_graph__mutmut_15': x_build_afripower_knowledge_graph__mutmut_15, 
    'x_build_afripower_knowledge_graph__mutmut_16': x_build_afripower_knowledge_graph__mutmut_16, 
    'x_build_afripower_knowledge_graph__mutmut_17': x_build_afripower_knowledge_graph__mutmut_17, 
    'x_build_afripower_knowledge_graph__mutmut_18': x_build_afripower_knowledge_graph__mutmut_18, 
    'x_build_afripower_knowledge_graph__mutmut_19': x_build_afripower_knowledge_graph__mutmut_19, 
    'x_build_afripower_knowledge_graph__mutmut_20': x_build_afripower_knowledge_graph__mutmut_20, 
    'x_build_afripower_knowledge_graph__mutmut_21': x_build_afripower_knowledge_graph__mutmut_21, 
    'x_build_afripower_knowledge_graph__mutmut_22': x_build_afripower_knowledge_graph__mutmut_22, 
    'x_build_afripower_knowledge_graph__mutmut_23': x_build_afripower_knowledge_graph__mutmut_23, 
    'x_build_afripower_knowledge_graph__mutmut_24': x_build_afripower_knowledge_graph__mutmut_24, 
    'x_build_afripower_knowledge_graph__mutmut_25': x_build_afripower_knowledge_graph__mutmut_25, 
    'x_build_afripower_knowledge_graph__mutmut_26': x_build_afripower_knowledge_graph__mutmut_26, 
    'x_build_afripower_knowledge_graph__mutmut_27': x_build_afripower_knowledge_graph__mutmut_27, 
    'x_build_afripower_knowledge_graph__mutmut_28': x_build_afripower_knowledge_graph__mutmut_28, 
    'x_build_afripower_knowledge_graph__mutmut_29': x_build_afripower_knowledge_graph__mutmut_29, 
    'x_build_afripower_knowledge_graph__mutmut_30': x_build_afripower_knowledge_graph__mutmut_30, 
    'x_build_afripower_knowledge_graph__mutmut_31': x_build_afripower_knowledge_graph__mutmut_31, 
    'x_build_afripower_knowledge_graph__mutmut_32': x_build_afripower_knowledge_graph__mutmut_32, 
    'x_build_afripower_knowledge_graph__mutmut_33': x_build_afripower_knowledge_graph__mutmut_33, 
    'x_build_afripower_knowledge_graph__mutmut_34': x_build_afripower_knowledge_graph__mutmut_34, 
    'x_build_afripower_knowledge_graph__mutmut_35': x_build_afripower_knowledge_graph__mutmut_35, 
    'x_build_afripower_knowledge_graph__mutmut_36': x_build_afripower_knowledge_graph__mutmut_36, 
    'x_build_afripower_knowledge_graph__mutmut_37': x_build_afripower_knowledge_graph__mutmut_37, 
    'x_build_afripower_knowledge_graph__mutmut_38': x_build_afripower_knowledge_graph__mutmut_38, 
    'x_build_afripower_knowledge_graph__mutmut_39': x_build_afripower_knowledge_graph__mutmut_39, 
    'x_build_afripower_knowledge_graph__mutmut_40': x_build_afripower_knowledge_graph__mutmut_40, 
    'x_build_afripower_knowledge_graph__mutmut_41': x_build_afripower_knowledge_graph__mutmut_41, 
    'x_build_afripower_knowledge_graph__mutmut_42': x_build_afripower_knowledge_graph__mutmut_42, 
    'x_build_afripower_knowledge_graph__mutmut_43': x_build_afripower_knowledge_graph__mutmut_43, 
    'x_build_afripower_knowledge_graph__mutmut_44': x_build_afripower_knowledge_graph__mutmut_44, 
    'x_build_afripower_knowledge_graph__mutmut_45': x_build_afripower_knowledge_graph__mutmut_45, 
    'x_build_afripower_knowledge_graph__mutmut_46': x_build_afripower_knowledge_graph__mutmut_46, 
    'x_build_afripower_knowledge_graph__mutmut_47': x_build_afripower_knowledge_graph__mutmut_47, 
    'x_build_afripower_knowledge_graph__mutmut_48': x_build_afripower_knowledge_graph__mutmut_48, 
    'x_build_afripower_knowledge_graph__mutmut_49': x_build_afripower_knowledge_graph__mutmut_49, 
    'x_build_afripower_knowledge_graph__mutmut_50': x_build_afripower_knowledge_graph__mutmut_50, 
    'x_build_afripower_knowledge_graph__mutmut_51': x_build_afripower_knowledge_graph__mutmut_51, 
    'x_build_afripower_knowledge_graph__mutmut_52': x_build_afripower_knowledge_graph__mutmut_52, 
    'x_build_afripower_knowledge_graph__mutmut_53': x_build_afripower_knowledge_graph__mutmut_53, 
    'x_build_afripower_knowledge_graph__mutmut_54': x_build_afripower_knowledge_graph__mutmut_54, 
    'x_build_afripower_knowledge_graph__mutmut_55': x_build_afripower_knowledge_graph__mutmut_55, 
    'x_build_afripower_knowledge_graph__mutmut_56': x_build_afripower_knowledge_graph__mutmut_56, 
    'x_build_afripower_knowledge_graph__mutmut_57': x_build_afripower_knowledge_graph__mutmut_57, 
    'x_build_afripower_knowledge_graph__mutmut_58': x_build_afripower_knowledge_graph__mutmut_58, 
    'x_build_afripower_knowledge_graph__mutmut_59': x_build_afripower_knowledge_graph__mutmut_59, 
    'x_build_afripower_knowledge_graph__mutmut_60': x_build_afripower_knowledge_graph__mutmut_60, 
    'x_build_afripower_knowledge_graph__mutmut_61': x_build_afripower_knowledge_graph__mutmut_61, 
    'x_build_afripower_knowledge_graph__mutmut_62': x_build_afripower_knowledge_graph__mutmut_62, 
    'x_build_afripower_knowledge_graph__mutmut_63': x_build_afripower_knowledge_graph__mutmut_63, 
    'x_build_afripower_knowledge_graph__mutmut_64': x_build_afripower_knowledge_graph__mutmut_64, 
    'x_build_afripower_knowledge_graph__mutmut_65': x_build_afripower_knowledge_graph__mutmut_65, 
    'x_build_afripower_knowledge_graph__mutmut_66': x_build_afripower_knowledge_graph__mutmut_66
}
x_build_afripower_knowledge_graph__mutmut_orig.__name__ = 'x_build_afripower_knowledge_graph'


# =============================================================================
# Public API
# =============================================================================

def build_afripower_knowledge_graph_dict(
    payloads: Iterable[Mapping[str, object]],
) -> Dict[str, object]:
    args = [payloads]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_afripower_knowledge_graph_dict__mutmut_orig, x_build_afripower_knowledge_graph_dict__mutmut_mutants, args, kwargs, None)


# =============================================================================
# Public API
# =============================================================================

def x_build_afripower_knowledge_graph_dict__mutmut_orig(
    payloads: Iterable[Mapping[str, object]],
) -> Dict[str, object]:
    return build_afripower_knowledge_graph(payloads).canonical_dict()


# =============================================================================
# Public API
# =============================================================================

def x_build_afripower_knowledge_graph_dict__mutmut_1(
    payloads: Iterable[Mapping[str, object]],
) -> Dict[str, object]:
    return build_afripower_knowledge_graph(None).canonical_dict()

x_build_afripower_knowledge_graph_dict__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_afripower_knowledge_graph_dict__mutmut_1': x_build_afripower_knowledge_graph_dict__mutmut_1
}
x_build_afripower_knowledge_graph_dict__mutmut_orig.__name__ = 'x_build_afripower_knowledge_graph_dict'


def build_graph_projection(
    payloads: Iterable[Mapping[str, object]],
) -> Dict[str, object]:
    args = [payloads]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_graph_projection__mutmut_orig, x_build_graph_projection__mutmut_mutants, args, kwargs, None)


def x_build_graph_projection__mutmut_orig(
    payloads: Iterable[Mapping[str, object]],
) -> Dict[str, object]:
    """
    Backward-compatible alias.
    """
    return build_afripower_knowledge_graph_dict(payloads)


def x_build_graph_projection__mutmut_1(
    payloads: Iterable[Mapping[str, object]],
) -> Dict[str, object]:
    """
    Backward-compatible alias.
    """
    return build_afripower_knowledge_graph_dict(None)

x_build_graph_projection__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_graph_projection__mutmut_1': x_build_graph_projection__mutmut_1
}
x_build_graph_projection__mutmut_orig.__name__ = 'x_build_graph_projection'