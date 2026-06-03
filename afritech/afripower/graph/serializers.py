"""
AFRIPower graph serializers.

Serializers convert read-only graph objects into deterministic dictionaries.

They must not:
- mutate graph objects
- validate runtime truth
- create authority
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from collections.abc import Mapping

from afritech.afripower.contracts.read_only_contract import (
    assert_read_only_contract,
)
from afritech.afripower.graph.constants import (
    GRAPH_DISPLAY_ONLY,
    GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
    GRAPH_PROJECTION_ONLY,
    GRAPH_READ_ONLY,
    GRAPH_REFERENCE_ONLY,
    assert_graph_constants,
)
from afritech.afripower.graph.models import (
    AFRIPowerGraph,
    AFRIPowerGraphEdge,
    AFRIPowerGraphNode,
)
from afritech.afripower.graph.query import AFRIPowerGraphQueryResult


class AFRIPowerGraphSerializationError(RuntimeError):
    """Raised when graph serialization fails."""


def _assert_serialization_boundary() -> None:
    assert_read_only_contract()
    assert_graph_constants()


def _boundary_metadata() -> dict[str, object]:
    return {
        "read_only": GRAPH_READ_ONLY,
        "reference_only": GRAPH_REFERENCE_ONLY,
        "display_only": GRAPH_DISPLAY_ONLY,
        "projection_only": GRAPH_PROJECTION_ONLY,
        "enterprise_intelligence_only": GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
        "creates_authority": False,
        "validates_truth": False,
        "executes_runtime": False,
        "mutates_graph": False,
        "mutates_artifacts": False,
        "influences_runtime": False,
        "influences_replay": False,
        "influences_proof": False,
        "influences_ci": False,
        "influences_governance": False,
    }


def serialize_graph_node(
    node: AFRIPowerGraphNode,
) -> dict[str, object]:
    """Serialize one graph node deterministically."""

    _assert_serialization_boundary()

    if not isinstance(node, AFRIPowerGraphNode):
        raise AFRIPowerGraphSerializationError(
            "expected AFRIPowerGraphNode"
        )

    data = node.canonical_dict()
    data.update(_boundary_metadata())
    return data


def serialize_graph_edge(
    edge: AFRIPowerGraphEdge,
) -> dict[str, object]:
    """Serialize one graph edge deterministically."""

    _assert_serialization_boundary()

    if not isinstance(edge, AFRIPowerGraphEdge):
        raise AFRIPowerGraphSerializationError(
            "expected AFRIPowerGraphEdge"
        )

    data = edge.canonical_dict()
    data.update(_boundary_metadata())
    return data


def serialize_graph(
    graph: AFRIPowerGraph,
) -> dict[str, object]:
    """Serialize an AFRIPower graph deterministically."""

    _assert_serialization_boundary()

    if not isinstance(graph, AFRIPowerGraph):
        raise AFRIPowerGraphSerializationError(
            "expected AFRIPowerGraph"
        )

    data = graph.canonical_dict()
    data.update(_boundary_metadata())
    data["nodes"] = tuple(
        serialize_graph_node(node)
        for node in graph.nodes
    )
    data["edges"] = tuple(
        serialize_graph_edge(edge)
        for edge in graph.edges
    )
    return data


def serialize_query_result(
    result: AFRIPowerGraphQueryResult,
) -> dict[str, object]:
    """Serialize a graph query result deterministically."""

    _assert_serialization_boundary()

    if not isinstance(result, AFRIPowerGraphQueryResult):
        raise AFRIPowerGraphSerializationError(
            "expected AFRIPowerGraphQueryResult"
        )

    data = result.canonical_dict()
    data.update(_boundary_metadata())
    data["nodes"] = tuple(
        serialize_graph_node(node)
        for node in result.nodes
    )
    data["edges"] = tuple(
        serialize_graph_edge(edge)
        for edge in result.edges
    )
    return data


def serialize_graph_summary(
    graph: AFRIPowerGraph,
) -> dict[str, object]:
    """Serialize graph summary counts only."""

    _assert_serialization_boundary()

    if not isinstance(graph, AFRIPowerGraph):
        raise AFRIPowerGraphSerializationError(
            "expected AFRIPowerGraph"
        )

    node_type_counts: dict[str, int] = {}
    edge_relation_counts: dict[str, int] = {}

    for node in graph.nodes:
        node_type_counts[node.node_type] = (
            node_type_counts.get(node.node_type, 0) + 1
        )

    for edge in graph.edges:
        edge_relation_counts[edge.relation] = (
            edge_relation_counts.get(edge.relation, 0) + 1
        )

    return {
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "edge_relation_counts": dict(sorted(edge_relation_counts.items())),
        **_boundary_metadata(),
    }


def ensure_serialized_graph_boundary(
    payload: Mapping[str, object],
) -> None:
    """
    Fail closed if serialized graph payload violates AFRIPower boundaries.
    """

    required_true = (
        "read_only",
        "reference_only",
        "display_only",
        "projection_only",
        "enterprise_intelligence_only",
    )

    required_false = (
        "creates_authority",
        "validates_truth",
        "executes_runtime",
        "mutates_graph",
        "mutates_artifacts",
        "influences_runtime",
        "influences_replay",
        "influences_proof",
        "influences_ci",
        "influences_governance",
    )

    for key in required_true:
        if payload.get(key) is not True:
            raise AFRIPowerGraphSerializationError(
                f"serialized graph field must be true: {key}"
            )

    for key in required_false:
        if payload.get(key) is not False:
            raise AFRIPowerGraphSerializationError(
                f"serialized graph field must be false: {key}"
            )


__all__ = [
    "AFRIPowerGraphSerializationError",
    "serialize_graph_node",
    "serialize_graph_edge",
    "serialize_graph",
    "serialize_query_result",
    "serialize_graph_summary",
    "ensure_serialized_graph_boundary",
]
