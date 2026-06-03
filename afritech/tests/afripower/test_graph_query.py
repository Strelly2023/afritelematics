from __future__ import annotations

from afritech.afripower.graph.projection import (
    build_graph_projection_from_mappings,
)
from afritech.afripower.graph.query import (
    AFRIPowerGraphQueryResult,
    count_edges_by_relation,
    count_nodes_by_type,
    find_edges_by_relation,
    find_incoming_edges,
    find_neighbors,
    find_nodes_by_type,
    find_outgoing_edges,
    get_node_by_id,
    query_graph,
    query_graph_dict,
    search_nodes,
)


def _sample_graph():
    return build_graph_projection_from_mappings(
        (
            {
                "execution_id": "exec.001",
                "traceability": [
                    {"type": "Proof", "id": "proof.001"},
                    {"type": "ADR", "id": "ADR-001"},
                    {"type": "Invariant", "id": "INVARIANT-001"},
                ],
            },
            {
                "execution_id": "exec.002",
                "traceability": [
                    {"type": "Proof", "id": "proof.002"},
                ],
            },
        )
    )


def test_get_node_by_id_returns_node():
    graph = _sample_graph()

    node = get_node_by_id(graph, "proof.001")

    assert node is not None
    assert node.node_id == "proof.001"
    assert node.node_type == "Proof"


def test_get_node_by_id_returns_none_when_missing():
    graph = _sample_graph()

    assert get_node_by_id(graph, "missing") is None


def test_find_nodes_by_type():
    graph = _sample_graph()

    nodes = find_nodes_by_type(graph, "Proof")

    assert len(nodes) == 2
    assert {node.node_id for node in nodes} == {
        "proof.001",
        "proof.002",
    }


def test_find_nodes_by_type_returns_empty_for_missing_type():
    graph = _sample_graph()

    assert find_nodes_by_type(graph, "Dashboard") == tuple()


def test_find_edges_by_relation():
    graph = _sample_graph()

    edges = find_edges_by_relation(graph, "references")

    assert len(edges) == 4
    assert all(edge.relation == "references" for edge in edges)


def test_find_edges_by_relation_returns_empty_for_missing_relation():
    graph = _sample_graph()

    assert find_edges_by_relation(graph, "supports") == tuple()


def test_find_outgoing_edges():
    graph = _sample_graph()

    edges = find_outgoing_edges(graph, "exec.001")

    assert len(edges) == 3
    assert {edge.target_id for edge in edges} == {
        "proof.001",
        "ADR-001",
        "INVARIANT-001",
    }


def test_find_incoming_edges():
    graph = _sample_graph()

    edges = find_incoming_edges(graph, "proof.001")

    assert len(edges) == 1
    assert edges[0].source_id == "exec.001"


def test_find_neighbors():
    graph = _sample_graph()

    neighbors = find_neighbors(graph, "exec.001")

    assert {node.node_id for node in neighbors} == {
        "proof.001",
        "ADR-001",
        "INVARIANT-001",
    }


def test_search_nodes_by_text():
    graph = _sample_graph()

    nodes = search_nodes(graph, "proof")

    assert {node.node_id for node in nodes} == {
        "proof.001",
        "proof.002",
    }


def test_search_nodes_returns_empty_for_blank_query():
    graph = _sample_graph()

    assert search_nodes(graph, "   ") == tuple()


def test_query_graph_by_node_id():
    graph = _sample_graph()

    result = query_graph(graph, node_id="exec.001")

    assert isinstance(result, AFRIPowerGraphQueryResult)
    assert result.query == "node_id:exec.001"
    assert len(result.nodes) == 1
    assert len(result.edges) == 3


def test_query_graph_by_node_type():
    graph = _sample_graph()

    result = query_graph(graph, node_type="Proof")

    assert result.query == "node_type:Proof"
    assert len(result.nodes) == 2
    assert len(result.edges) == 2


def test_query_graph_by_relation():
    graph = _sample_graph()

    result = query_graph(graph, relation="references")

    assert result.query == "relation:references"
    assert len(result.edges) == 4
    assert len(result.nodes) == 6


def test_query_graph_by_text():
    graph = _sample_graph()

    result = query_graph(graph, text="ADR")

    assert result.query == "text:ADR"
    assert len(result.nodes) == 1
    assert result.nodes[0].node_id == "ADR-001"


def test_query_graph_without_filter_returns_all():
    graph = _sample_graph()

    result = query_graph(graph)

    assert result.query == "all"
    assert len(result.nodes) == len(graph.nodes)
    assert len(result.edges) == len(graph.edges)


def test_query_graph_result_canonical_dict_preserves_boundary():
    graph = _sample_graph()

    result = query_graph(graph, node_id="exec.001")
    data = result.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_graph"] is False


def test_query_graph_dict():
    graph = _sample_graph()

    data = query_graph_dict(graph, node_id="exec.001")

    assert data["query"] == "node_id:exec.001"
    assert data["read_only"] is True
    assert data["creates_authority"] is False
    assert len(data["nodes"]) == 1
    assert len(data["edges"]) == 3


def test_count_nodes_by_type():
    graph = _sample_graph()

    counts = count_nodes_by_type(graph)

    assert counts["Execution"] == 2
    assert counts["Proof"] == 2
    assert counts["ADR"] == 1
    assert counts["Invariant"] == 1


def test_count_edges_by_relation():
    graph = _sample_graph()

    counts = count_edges_by_relation(graph)

    assert counts == {"references": 4}


def test_query_graph_is_deterministic():
    graph = _sample_graph()

    first = query_graph_dict(graph, relation="references")
    second = query_graph_dict(graph, relation="references")

    assert first == second
