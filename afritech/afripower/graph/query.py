"""
AFRIPower read-only graph query utilities.

Queries are observational only.

They must not:
- mutate the graph
- validate truth
- create authority
- influence runtime/replay/proof/CI/governance
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

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


class AFRIPowerGraphQueryError(RuntimeError):
    """Raised when a read-only graph query is invalid."""


@dataclass(frozen=True)
class AFRIPowerGraphQueryResult:
    """Immutable read-only graph query result."""

    nodes: tuple[AFRIPowerGraphNode, ...]
    edges: tuple[AFRIPowerGraphEdge, ...]
    query: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "query": self.query,
            "read_only": GRAPH_READ_ONLY,
            "reference_only": GRAPH_REFERENCE_ONLY,
            "display_only": GRAPH_DISPLAY_ONLY,
            "projection_only": GRAPH_PROJECTION_ONLY,
            "enterprise_intelligence_only": GRAPH_ENTERPRISE_INTELLIGENCE_ONLY,
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_graph": False,
            "nodes": [node.canonical_dict() for node in self.nodes],
            "edges": [edge.canonical_dict() for edge in self.edges],
        }


def _assert_query_boundary() -> None:
    assert_read_only_contract()
    assert_graph_constants()


def get_node_by_id(
    graph: AFRIPowerGraph,
    node_id: str,
) -> AFRIPowerGraphNode | None:
    """Return one node by id, without mutation."""

    _assert_query_boundary()

    for node in graph.nodes:
        if node.node_id == node_id:
            return node

    return None


def find_nodes_by_type(
    graph: AFRIPowerGraph,
    node_type: str,
) -> tuple[AFRIPowerGraphNode, ...]:
    """Return all nodes with a matching type."""

    _assert_query_boundary()

    return tuple(
        node
        for node in graph.nodes
        if node.node_type == node_type
    )


def find_edges_by_relation(
    graph: AFRIPowerGraph,
    relation: str,
) -> tuple[AFRIPowerGraphEdge, ...]:
    """Return all edges with a matching relation."""

    _assert_query_boundary()

    return tuple(
        edge
        for edge in graph.edges
        if edge.relation == relation
    )


def find_outgoing_edges(
    graph: AFRIPowerGraph,
    node_id: str,
) -> tuple[AFRIPowerGraphEdge, ...]:
    """Return outgoing edges from a node."""

    _assert_query_boundary()

    return tuple(
        edge
        for edge in graph.edges
        if edge.source_id == node_id
    )


def find_incoming_edges(
    graph: AFRIPowerGraph,
    node_id: str,
) -> tuple[AFRIPowerGraphEdge, ...]:
    """Return incoming edges to a node."""

    _assert_query_boundary()

    return tuple(
        edge
        for edge in graph.edges
        if edge.target_id == node_id
    )


def find_neighbors(
    graph: AFRIPowerGraph,
    node_id: str,
) -> tuple[AFRIPowerGraphNode, ...]:
    """Return directly connected neighboring nodes."""

    _assert_query_boundary()

    neighbor_ids = {
        edge.target_id
        for edge in graph.edges
        if edge.source_id == node_id
    } | {
        edge.source_id
        for edge in graph.edges
        if edge.target_id == node_id
    }

    return tuple(
        node
        for node in graph.nodes
        if node.node_id in neighbor_ids
    )


def search_nodes(
    graph: AFRIPowerGraph,
    text: str,
) -> tuple[AFRIPowerGraphNode, ...]:
    """Search nodes by id, type, label, or metadata text."""

    _assert_query_boundary()

    normalized = text.strip().lower()

    if not normalized:
        return tuple()

    results: list[AFRIPowerGraphNode] = []

    for node in graph.nodes:
        metadata_text = " ".join(
            f"{key} {value}"
            for key, value in node.metadata
        ).lower()

        searchable = " ".join(
            (
                node.node_id,
                node.node_type,
                node.label or "",
                metadata_text,
            )
        ).lower()

        if normalized in searchable:
            results.append(node)

    return tuple(results)


def query_graph(
    graph: AFRIPowerGraph,
    *,
    node_id: str | None = None,
    node_type: str | None = None,
    relation: str | None = None,
    text: str | None = None,
) -> AFRIPowerGraphQueryResult:
    """
    Run a deterministic read-only graph query.

    Query precedence:
    1. node_id
    2. node_type
    3. relation
    4. text
    5. full graph
    """

    _assert_query_boundary()

    if node_id:
        node = get_node_by_id(graph, node_id)
        nodes = (node,) if node is not None else tuple()
        edges = tuple(
            edge
            for edge in graph.edges
            if edge.source_id == node_id or edge.target_id == node_id
        )
        return AFRIPowerGraphQueryResult(
            nodes=nodes,
            edges=edges,
            query=f"node_id:{node_id}",
        )

    if node_type:
        nodes = find_nodes_by_type(graph, node_type)
        node_ids = {node.node_id for node in nodes}
        edges = tuple(
            edge
            for edge in graph.edges
            if edge.source_id in node_ids or edge.target_id in node_ids
        )
        return AFRIPowerGraphQueryResult(
            nodes=nodes,
            edges=edges,
            query=f"node_type:{node_type}",
        )

    if relation:
        edges = find_edges_by_relation(graph, relation)
        node_ids = {
            edge.source_id
            for edge in edges
        } | {
            edge.target_id
            for edge in edges
        }
        nodes = tuple(
            node
            for node in graph.nodes
            if node.node_id in node_ids
        )
        return AFRIPowerGraphQueryResult(
            nodes=nodes,
            edges=edges,
            query=f"relation:{relation}",
        )

    if text:
        nodes = search_nodes(graph, text)
        node_ids = {node.node_id for node in nodes}
        edges = tuple(
            edge
            for edge in graph.edges
            if edge.source_id in node_ids or edge.target_id in node_ids
        )
        return AFRIPowerGraphQueryResult(
            nodes=nodes,
            edges=edges,
            query=f"text:{text}",
        )

    return AFRIPowerGraphQueryResult(
        nodes=tuple(graph.nodes),
        edges=tuple(graph.edges),
        query="all",
    )


def query_graph_dict(
    graph: AFRIPowerGraph,
    *,
    node_id: str | None = None,
    node_type: str | None = None,
    relation: str | None = None,
    text: str | None = None,
) -> dict[str, object]:
    """Return query result as canonical dictionary."""

    return query_graph(
        graph,
        node_id=node_id,
        node_type=node_type,
        relation=relation,
        text=text,
    ).canonical_dict()


def count_nodes_by_type(
    graph: AFRIPowerGraph,
) -> dict[str, int]:
    """Return deterministic counts by node type."""

    _assert_query_boundary()

    counts: dict[str, int] = {}

    for node in graph.nodes:
        counts[node.node_type] = counts.get(node.node_type, 0) + 1

    return dict(sorted(counts.items()))


def count_edges_by_relation(
    graph: AFRIPowerGraph,
) -> dict[str, int]:
    """Return deterministic counts by edge relation."""

    _assert_query_boundary()

    counts: dict[str, int] = {}

    for edge in graph.edges:
        counts[edge.relation] = counts.get(edge.relation, 0) + 1

    return dict(sorted(counts.items()))


__all__ = [
    "AFRIPowerGraphQueryError",
    "AFRIPowerGraphQueryResult",
    "get_node_by_id",
    "find_nodes_by_type",
    "find_edges_by_relation",
    "find_outgoing_edges",
    "find_incoming_edges",
    "find_neighbors",
    "search_nodes",
    "query_graph",
    "query_graph_dict",
    "count_nodes_by_type",
    "count_edges_by_relation",
]
