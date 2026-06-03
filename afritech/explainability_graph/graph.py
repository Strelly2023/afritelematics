"""
Read-only Explainability Graph builder.

The graph is a display-only explanatory surface.

Constitutional Law
------------------
Graph explains.
Graph visualizes.
Graph does not govern.
Graph does not validate.
Graph does not execute.
Graph does not influence runtime, replay, proof, CI, or governance authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from afritech.explainability_graph.constants import (
    GRAPH_DATA_CLASSIFICATION,
    GRAPH_OUTPUT_CLASSIFICATION,
    GRAPH_RELATIONSHIP_CLASSIFICATION,
    GRAPH_STATUS,
    INVARIANT_GRAPH_CANNOT_INFLUENCE_PROOF,
    INVARIANT_GRAPH_CANNOT_INFLUENCE_REPLAY,
    INVARIANT_GRAPH_CANNOT_INFLUENCE_RUNTIME,
    INVARIANT_GRAPH_IS_DISPLAY_ONLY,
    INVARIANT_GRAPH_IS_NON_AUTHORITATIVE,
    INVARIANT_GRAPH_IS_READ_ONLY,
    RUNTIME_AUTHORITY,
    VALIDATION_AUTHORITY,
)
from afritech.explainability_graph.edge import (
    GraphEdge,
    build_graph_edge,
)
from afritech.explainability_graph.node import (
    GraphNode,
    build_graph_node,
)


TRACEABILITY_FIELD = "governance_traceability"


@dataclass(frozen=True)
class ExplainabilityGraph:
    """Immutable read-only explainability graph."""

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    def canonical_dict(self) -> dict[str, object]:
        """Return canonical display-only graph representation."""

        return {
            "graph_status": GRAPH_STATUS,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "relationship_classification": GRAPH_RELATIONSHIP_CLASSIFICATION,
            "read_only": INVARIANT_GRAPH_IS_READ_ONLY,
            "display_only": INVARIANT_GRAPH_IS_DISPLAY_ONLY,
            "non_authoritative": INVARIANT_GRAPH_IS_NON_AUTHORITATIVE,
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
            "influences_runtime": (
                not INVARIANT_GRAPH_CANNOT_INFLUENCE_RUNTIME
            ),
            "influences_replay": (
                not INVARIANT_GRAPH_CANNOT_INFLUENCE_REPLAY
            ),
            "influences_proof": (
                not INVARIANT_GRAPH_CANNOT_INFLUENCE_PROOF
            ),
            "nodes": [node.canonical_dict() for node in self.nodes],
            "edges": [edge.canonical_dict() for edge in self.edges],
        }


def _safe_str(value: object, fallback: str) -> str:
    """Return deterministic string value without raising."""

    if isinstance(value, str) and value.strip():
        return value.strip()

    return fallback


def _normalize_node_type(value: str) -> str:
    """Normalize governance reference types into allowed graph node types.

    This is display compatibility only.
    It does not validate governance truth or create authority.
    """

    normalized = value.strip().upper()

    mapping = {
        "EXECUTION": "Execution",
        "ADR": "ADR",
        "INVARIANT": "Invariant",
        "INVARIANTS": "Invariant",
        "RULE": "Rule",
        "RULES": "Rule",
        "BIND": "Binding",
        "BINDING": "Binding",
        "BINDINGS": "Binding",
        "RECEIPT": "Receipt",
        "RECEIPTS": "Receipt",
        "PROOF": "Proof",
        "PROOFS": "Proof",
    }

    return mapping.get(normalized, value.strip())


def _extract_references(
    payload: Mapping[str, object],
) -> tuple[dict[str, str], ...]:
    """Extract governance references from a receipt/explanation payload.

    Extraction is display-only.
    It does not validate governance truth or resolve authority.
    """

    raw_refs = payload.get(TRACEABILITY_FIELD, [])

    if not isinstance(raw_refs, Sequence) or isinstance(
        raw_refs,
        (str, bytes),
    ):
        return ()

    references: list[dict[str, str]] = []

    for raw_ref in raw_refs:
        if not isinstance(raw_ref, Mapping):
            continue

        ref_type = raw_ref.get("type")
        ref_id = raw_ref.get("id")

        if not isinstance(ref_type, str):
            continue

        if not isinstance(ref_id, str):
            continue

        ref_type = ref_type.strip()
        ref_id = ref_id.strip()

        if not ref_type or not ref_id:
            continue

        references.append(
            {
                "type": ref_type,
                "id": ref_id,
            }
        )

    return tuple(references)


def build_explainability_graph(
    payload: Mapping[str, object],
) -> ExplainabilityGraph:
    """Build an immutable read-only explainability graph.

    Accepted payloads may be receipts or explanation payloads containing:

    ```text
    execution_id
    governance_traceability
    ```

    The graph only visualizes references.
    It does not mutate the input payload.
    """

    execution_id = _safe_str(
        payload.get("execution_id"),
        fallback="unknown-execution",
    )

    execution_node = build_graph_node(
        node_type="Execution",
        node_id=execution_id,
        label=execution_id,
    )

    nodes: list[GraphNode] = [execution_node]
    edges: list[GraphEdge] = []

    seen_node_keys: set[tuple[str, str]] = {
        ("Execution", execution_id),
    }

    references = _extract_references(payload)

    for reference in references:
        ref_type = _normalize_node_type(reference["type"])
        ref_id = reference["id"]

        node_key = (ref_type, ref_id)

        if node_key not in seen_node_keys:
            nodes.append(
                build_graph_node(
                    node_type=ref_type,
                    node_id=ref_id,
                    label=ref_id,
                )
            )
            seen_node_keys.add(node_key)

        edges.append(
            build_graph_edge(
                source_id=execution_id,
                target_id=ref_id,
                relation="governed_by",
            )
        )

    return ExplainabilityGraph(
        nodes=tuple(nodes),
        edges=tuple(edges),
    )


def build_explainability_graph_dict(
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Build canonical graph dictionary for display/API use."""

    return build_explainability_graph(payload).canonical_dict()


def build_graph_from_receipt(
    receipt: Mapping[str, object],
) -> dict[str, object]:
    """Compatibility helper for receipt-shaped payloads."""

    return build_explainability_graph_dict(receipt)


def build_graph_from_explanation(
    explanation_payload: Mapping[str, object],
) -> dict[str, object]:
    """Compatibility helper for explanation-shaped payloads."""

    return build_explainability_graph_dict(explanation_payload)