from __future__ import annotations

from afritech.afripower.graph.projection import (
    build_graph_projection_from_mappings,
)
from afritech.afripower.graph.query import (
    count_edges_by_relation,
    count_nodes_by_type,
    query_graph_dict,
)


def _graph():
    return build_graph_projection_from_mappings(
        (
            {
                "execution_id": "exec-1",
                "governance_traceability": [
                    {"type": "ADR", "id": "ADR-1"},
                    {"type": "RULE", "id": "RULE-1"},
                ],
            },
        )
    )


def test_query_summary_counts_nodes_and_edges():
    graph = _graph()

    assert count_nodes_by_type(graph) == {
        "ADR": 1,
        "Execution": 1,
        "Rule": 1,
    }
    assert count_edges_by_relation(graph) == {
        "references": 2,
    }


def test_query_by_node_type():
    result = query_graph_dict(_graph(), node_type="ADR")

    assert result["read_only"] is True
    assert result["creates_authority"] is False
    assert result["query"] == "node_type:ADR"
    assert len(result["nodes"]) == 1


def test_query_all_is_deterministic():
    graph = _graph()

    assert query_graph_dict(graph) == query_graph_dict(graph)
