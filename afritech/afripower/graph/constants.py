"""
AFRIPower graph constants.

The AFRIPower graph is a read-only enterprise intelligence projection.

It may represent relationships between execution, proof, governance,
traceability, and explainability artifacts.

It must not create authority, validate truth, mutate artifacts, or influence
runtime/replay/proof/CI/governance behavior.
"""

from __future__ import annotations

from typing import Tuple

from afritech.afripower.constants import (
    AFRIPOWER_PROJECTION_STATUS,
    DISPLAY_ONLY,
    ENTERPRISE_INTELLIGENCE_ONLY,
    GRAPH_DATA_CLASSIFICATION,
    GRAPH_OUTPUT_CLASSIFICATION,
    GRAPH_RELATIONSHIP_CLASSIFICATION,
    LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    PROJECTION_CREATES_AUTHORITY,
    PROJECTION_ONLY,
    READ_ONLY,
    REFERENCE_ONLY,
)


GRAPH_COMPONENT = "AFRIPowerGraph"
GRAPH_COMPONENT_ID = "afritech.afripower.graph"
GRAPH_VERSION = "1.0"

GRAPH_STATUS = AFRIPOWER_PROJECTION_STATUS
GRAPH_MODE = "READ_ONLY_ENTERPRISE_INTELLIGENCE_GRAPH"

GRAPH_READ_ONLY = READ_ONLY
GRAPH_REFERENCE_ONLY = REFERENCE_ONLY
GRAPH_DISPLAY_ONLY = DISPLAY_ONLY
GRAPH_PROJECTION_ONLY = PROJECTION_ONLY
GRAPH_ENTERPRISE_INTELLIGENCE_ONLY = ENTERPRISE_INTELLIGENCE_ONLY

GRAPH_AUTHORITATIVE = False
GRAPH_CREATES_AUTHORITY = PROJECTION_CREATES_AUTHORITY
GRAPH_VALIDATES_TRUTH = False
GRAPH_EXECUTES_RUNTIME = False
GRAPH_MUTATES_ARTIFACTS = False
GRAPH_INFLUENCES_RUNTIME = False
GRAPH_INFLUENCES_REPLAY = False
GRAPH_INFLUENCES_PROOF = False
GRAPH_INFLUENCES_CI = False
GRAPH_INFLUENCES_GOVERNANCE = False

GRAPH_NODE_TYPES: Tuple[str, ...] = (
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
    "Dashboard",
    "Metric",
    "Insight",
)

GRAPH_EDGE_TYPES: Tuple[str, ...] = (
    "references",
    "explains",
    "supports",
    "projects",
    "depends_on",
    "linked_to",
    "impacts",
    "summarizes",
    "observes",
)

GRAPH_REQUIRED_NODE_KEYS: Tuple[str, ...] = (
    "node_id",
    "node_type",
)

GRAPH_REQUIRED_EDGE_KEYS: Tuple[str, ...] = (
    "source_id",
    "target_id",
    "relation",
)

GRAPH_CLASSIFICATION_METADATA = {
    "component": GRAPH_COMPONENT,
    "component_id": GRAPH_COMPONENT_ID,
    "version": GRAPH_VERSION,
    "status": GRAPH_STATUS,
    "mode": GRAPH_MODE,
    "data_classification": GRAPH_DATA_CLASSIFICATION,
    "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
    "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
    "read_only": GRAPH_READ_ONLY,
    "reference_only": GRAPH_REFERENCE_ONLY,
    "display_only": GRAPH_DISPLAY_ONLY,
    "projection_only": GRAPH_PROJECTION_ONLY,
    "enterprise_intelligence_only": GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
    "non_authoritative": LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    "consumes_authority_only": LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    "authoritative": GRAPH_AUTHORITATIVE,
    "creates_authority": GRAPH_CREATES_AUTHORITY,
    "validates_truth": GRAPH_VALIDATES_TRUTH,
    "executes_runtime": GRAPH_EXECUTES_RUNTIME,
    "mutates_artifacts": GRAPH_MUTATES_ARTIFACTS,
    "influences_runtime": GRAPH_INFLUENCES_RUNTIME,
    "influences_replay": GRAPH_INFLUENCES_REPLAY,
    "influences_proof": GRAPH_INFLUENCES_PROOF,
    "influences_ci": GRAPH_INFLUENCES_CI,
    "influences_governance": GRAPH_INFLUENCES_GOVERNANCE,
}


def graph_metadata() -> dict[str, object]:
    """Return deterministic AFRIPower graph metadata."""

    return dict(GRAPH_CLASSIFICATION_METADATA)


def assert_graph_constants() -> None:
    """Fail closed if graph constants violate AFRIPower boundaries."""

    forbidden_true_flags = (
        GRAPH_AUTHORITATIVE,
        GRAPH_CREATES_AUTHORITY,
        GRAPH_VALIDATES_TRUTH,
        GRAPH_EXECUTES_RUNTIME,
        GRAPH_MUTATES_ARTIFACTS,
        GRAPH_INFLUENCES_RUNTIME,
        GRAPH_INFLUENCES_REPLAY,
        GRAPH_INFLUENCES_PROOF,
        GRAPH_INFLUENCES_CI,
        GRAPH_INFLUENCES_GOVERNANCE,
    )

    if any(forbidden_true_flags):
        raise RuntimeError("AFRIPower graph authority boundary violation")

    required_true_flags = (
        GRAPH_READ_ONLY,
        GRAPH_REFERENCE_ONLY,
        GRAPH_DISPLAY_ONLY,
        GRAPH_PROJECTION_ONLY,
        GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
    )

    if not all(required_true_flags):
        raise RuntimeError("AFRIPower graph safety boundary violation")


__all__ = [
    "GRAPH_COMPONENT",
    "GRAPH_COMPONENT_ID",
    "GRAPH_VERSION",
    "GRAPH_STATUS",
    "GRAPH_MODE",
    "GRAPH_READ_ONLY",
    "GRAPH_REFERENCE_ONLY",
    "GRAPH_DISPLAY_ONLY",
    "GRAPH_PROJECTION_ONLY",
    "GRAPH_ENTERPRISE_INTELLIGENCE_ONLY",
    "GRAPH_AUTHORITATIVE",
    "GRAPH_CREATES_AUTHORITY",
    "GRAPH_VALIDATES_TRUTH",
    "GRAPH_EXECUTES_RUNTIME",
    "GRAPH_MUTATES_ARTIFACTS",
    "GRAPH_INFLUENCES_RUNTIME",
    "GRAPH_INFLUENCES_REPLAY",
    "GRAPH_INFLUENCES_PROOF",
    "GRAPH_INFLUENCES_CI",
    "GRAPH_INFLUENCES_GOVERNANCE",
    "GRAPH_NODE_TYPES",
    "GRAPH_EDGE_TYPES",
    "GRAPH_REQUIRED_NODE_KEYS",
    "GRAPH_REQUIRED_EDGE_KEYS",
    "GRAPH_CLASSIFICATION_METADATA",
    "graph_metadata",
    "assert_graph_constants",
]
