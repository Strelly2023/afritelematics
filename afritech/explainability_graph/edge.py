"""
Read-only Explainability Graph edge model.

Edges represent display-only relationships between graph nodes.

Constitutional Law
------------------
Edges explain relationships.
Edges do not govern relationships.
Edges do not validate truth.
Edges do not influence execution.
Edges do not influence replay.
Edges do not influence proof admissibility.
"""

from __future__ import annotations

from dataclasses import dataclass

from afritech.explainability_graph.constants import (
    ALLOWED_EDGE_TYPES,
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


@dataclass(frozen=True)
class GraphEdge:
    """
    Immutable display-only graph edge.
    """

    source_id: str
    target_id: str
    relation: str

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("graph edge source_id is required")

        if not self.target_id:
            raise ValueError("graph edge target_id is required")

        if self.relation not in ALLOWED_EDGE_TYPES:
            raise ValueError(
                f"unsupported graph edge relation: {self.relation}"
            )

    def canonical_dict(self) -> dict[str, object]:
        """
        Return canonical display-only edge representation.
        """

        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "graph_status": GRAPH_STATUS,
            "relationship_classification": (
                GRAPH_RELATIONSHIP_CLASSIFICATION
            ),
            "data_classification": GRAPH_DATA_CLASSIFICATION,
            "output_classification": GRAPH_OUTPUT_CLASSIFICATION,
            "read_only": INVARIANT_GRAPH_IS_READ_ONLY,
            "display_only": INVARIANT_GRAPH_IS_DISPLAY_ONLY,
            "non_authoritative": (
                INVARIANT_GRAPH_IS_NON_AUTHORITATIVE
            ),
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
        }


def build_graph_edge(
    source_id: str,
    target_id: str,
    relation: str,
) -> GraphEdge:
    """
    Build immutable display-only graph edge.
    """

    return GraphEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
    )


def graph_edge_to_dict(
    edge: GraphEdge,
) -> dict[str, object]:
    """
    Serialize graph edge without introducing authority.
    """

    return edge.canonical_dict()