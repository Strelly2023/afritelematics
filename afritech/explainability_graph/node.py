"""Read-only Explainability Graph node model.

Nodes are display-only references used to visualize relationships between
executions, governance artifacts, receipts, and proofs.

They are not runtime authority.
They are not validation authority.
They are not proof authority.
"""

from __future__ import annotations

from dataclasses import dataclass

from afritech.explainability_graph.constants import (
    ALLOWED_NODE_TYPES,
    GRAPH_DATA_CLASSIFICATION,
    GRAPH_OUTPUT_CLASSIFICATION,
    GRAPH_STATUS,
    INVARIANT_GRAPH_IS_DISPLAY_ONLY,
    INVARIANT_GRAPH_IS_NON_AUTHORITATIVE,
    INVARIANT_GRAPH_IS_READ_ONLY,
    RUNTIME_AUTHORITY,
    VALIDATION_AUTHORITY,
)


@dataclass(frozen=True)
class GraphNode:
    """Immutable display-only graph node."""

    node_type: str
    node_id: str
    label: str | None = None

    def __post_init__(self) -> None:
        if self.node_type not in ALLOWED_NODE_TYPES:
            raise ValueError(f"unsupported graph node type: {self.node_type}")

        if not self.node_id:
            raise ValueError("graph node id is required")

    def canonical_dict(self) -> dict[str, object]:
        """Return canonical display-only node representation."""

        return {
            "type": self.node_type,
            "id": self.node_id,
            "label": self.label or self.node_id,
            "graph_status": GRAPH_STATUS,
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "read_only": INVARIANT_GRAPH_IS_READ_ONLY,
            "display_only": INVARIANT_GRAPH_IS_DISPLAY_ONLY,
            "non_authoritative": INVARIANT_GRAPH_IS_NON_AUTHORITATIVE,
            "runtime_authority": RUNTIME_AUTHORITY,
            "validation_authority": VALIDATION_AUTHORITY,
        }


def build_graph_node(
    node_type: str,
    node_id: str,
    label: str | None = None,
) -> GraphNode:
    """Build an immutable read-only graph node."""

    return GraphNode(
        node_type=node_type,
        node_id=node_id,
        label=label,
    )


def graph_node_to_dict(node: GraphNode) -> dict[str, object]:
    """Serialize a graph node without adding authority semantics."""

    return node.canonical_dict()