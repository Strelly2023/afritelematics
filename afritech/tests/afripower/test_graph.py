from __future__ import annotations

from afritech.afripower.graph.projection import project_graph


def _build_sample_receipts():
    return (
        {
            "execution_id": "exec-1",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-1"},
                {"type": "RULE", "id": "RULE-1"},
            ],
        },
    )


def test_graph_projection_executes():
    graph = project_graph(_build_sample_receipts())

    assert graph["read_only"] is True
    assert graph["reference_only"] is True
    assert graph["display_only"] is True
    assert graph["projection_only"] is True
    assert graph["enterprise_intelligence_only"] is True

    assert graph["creates_authority"] is False
    assert graph["validates_truth"] is False
    assert graph["executes_runtime"] is False
    assert graph["mutates_artifacts"] is False

    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)


def test_graph_nodes_have_expected_structure():
    graph = project_graph(_build_sample_receipts())

    for node in graph["nodes"]:
        assert "node_id" in node
        assert "node_type" in node
        assert isinstance(node["node_id"], str)
        assert isinstance(node["node_type"], str)


def test_graph_edges_have_expected_structure():
    graph = project_graph(_build_sample_receipts())

    for edge in graph["edges"]:
        assert "source_id" in edge
        assert "target_id" in edge
        assert "relation" in edge
        assert isinstance(edge["source_id"], str)
        assert isinstance(edge["target_id"], str)


def test_graph_projection_is_deterministic():
    receipts = _build_sample_receipts()

    assert project_graph(receipts) == project_graph(receipts)


def test_graph_projection_empty_input():
    graph = project_graph(())

    assert graph["nodes"] == []
    assert graph["edges"] == []
    assert graph["read_only"] is True
    assert graph["creates_authority"] is False


def test_graph_projection_multiple_receipts():
    receipts = (
        {
            "execution_id": "exec-1",
            "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
        },
        {
            "execution_id": "exec-2",
            "governance_traceability": [{"type": "RULE", "id": "RULE-1"}],
        },
    )

    graph = project_graph(receipts)

    assert len(graph["nodes"]) >= 4
    assert len(graph["edges"]) >= 2


def test_graph_projection_handles_duplicates():
    graph = project_graph(
        (
            {
                "execution_id": "exec-1",
                "governance_traceability": [
                    {"type": "ADR", "id": "ADR-1"},
                    {"type": "ADR", "id": "ADR-1"},
                ],
            },
        )
    )

    ids = [node["node_id"] for node in graph["nodes"]]
    assert ids.count("ADR-1") == 1


def test_graph_projection_order_stability():
    graph1 = project_graph(_build_sample_receipts())
    graph2 = project_graph(_build_sample_receipts())

    assert [n["node_id"] for n in graph1["nodes"]] == [
        n["node_id"] for n in graph2["nodes"]
    ]
    assert [(e["source_id"], e["target_id"]) for e in graph1["edges"]] == [
        (e["source_id"], e["target_id"]) for e in graph2["edges"]
    ]
