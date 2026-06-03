from __future__ import annotations

import pytest

from afritech.afripower.graph.models import (
    AFRIPowerGraph,
    AFRIPowerGraphEdge,
    AFRIPowerGraphModelError,
    AFRIPowerGraphNode,
    build_graph_dict_from_mappings,
    build_graph_from_mappings,
)


def test_graph_node_accepts_valid_payload():
    node = AFRIPowerGraphNode(
        node_id="exec.001",
        node_type="Execution",
    )

    assert node.node_id == "exec.001"
    assert node.node_type == "Execution"


def test_graph_node_rejects_empty_id():
    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraphNode(
            node_id="",
            node_type="Execution",
        )


def test_graph_node_rejects_invalid_type():
    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraphNode(
            node_id="node.001",
            node_type="InvalidType",
        )


def test_graph_node_canonical_dict_preserves_boundary():
    node = AFRIPowerGraphNode(
        node_id="exec.001",
        node_type="Execution",
    )

    data = node.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False


def test_graph_node_label_defaults_to_id():
    node = AFRIPowerGraphNode(
        node_id="proof.001",
        node_type="Proof",
    )

    assert node.canonical_dict()["label"] == "proof.001"


def test_graph_node_accepts_label():
    node = AFRIPowerGraphNode(
        node_id="proof.001",
        node_type="Proof",
        label="Proof Node",
    )

    assert node.canonical_dict()["label"] == "Proof Node"


def test_graph_node_metadata_is_sorted_and_deterministic():
    node = AFRIPowerGraphNode(
        node_id="proof.001",
        node_type="Proof",
        metadata=(
            ("z", 1),
            ("a", 2),
        ),
    )

    assert node.metadata == (
        ("a", 2),
        ("z", 1),
    )


def test_graph_node_from_mapping_accepts_id_aliases():
    node = AFRIPowerGraphNode.from_mapping(
        {
            "id": "exec.001",
            "type": "Execution",
        }
    )

    assert node.node_id == "exec.001"
    assert node.node_type == "Execution"


def test_graph_node_from_mapping_rejects_bad_metadata():
    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraphNode.from_mapping(
            {
                "node_id": "exec.001",
                "node_type": "Execution",
                "metadata": "bad",
            }
        )


def test_graph_edge_accepts_valid_payload():
    edge = AFRIPowerGraphEdge(
        source_id="exec.001",
        target_id="proof.001",
        relation="references",
    )

    assert edge.source_id == "exec.001"
    assert edge.target_id == "proof.001"
    assert edge.relation == "references"


def test_graph_edge_rejects_empty_source():
    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraphEdge(
            source_id="",
            target_id="proof.001",
            relation="references",
        )


def test_graph_edge_rejects_empty_target():
    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraphEdge(
            source_id="exec.001",
            target_id="",
            relation="references",
        )


def test_graph_edge_rejects_invalid_relation():
    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraphEdge(
            source_id="exec.001",
            target_id="proof.001",
            relation="executes",
        )


def test_graph_edge_canonical_dict_preserves_boundary():
    edge = AFRIPowerGraphEdge(
        source_id="exec.001",
        target_id="proof.001",
        relation="references",
    )

    data = edge.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False
    assert data["influences_runtime"] is False
    assert data["influences_replay"] is False
    assert data["influences_proof"] is False
    assert data["influences_ci"] is False
    assert data["influences_governance"] is False


def test_graph_edge_metadata_is_sorted_and_deterministic():
    edge = AFRIPowerGraphEdge(
        source_id="exec.001",
        target_id="proof.001",
        relation="references",
        metadata=(
            ("z", 1),
            ("a", 2),
        ),
    )

    assert edge.metadata == (
        ("a", 2),
        ("z", 1),
    )


def test_graph_edge_from_mapping_rejects_bad_metadata():
    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraphEdge.from_mapping(
            {
                "source_id": "exec.001",
                "target_id": "proof.001",
                "relation": "references",
                "metadata": "bad",
            }
        )


def test_graph_accepts_valid_nodes_and_edges():
    node_a = AFRIPowerGraphNode(
        node_id="exec.001",
        node_type="Execution",
    )
    node_b = AFRIPowerGraphNode(
        node_id="proof.001",
        node_type="Proof",
    )
    edge = AFRIPowerGraphEdge(
        source_id="exec.001",
        target_id="proof.001",
        relation="references",
    )

    graph = AFRIPowerGraph(
        nodes=(node_a, node_b),
        edges=(edge,),
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_graph_rejects_edge_with_missing_source():
    node = AFRIPowerGraphNode(
        node_id="proof.001",
        node_type="Proof",
    )
    edge = AFRIPowerGraphEdge(
        source_id="exec.001",
        target_id="proof.001",
        relation="references",
    )

    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraph(
            nodes=(node,),
            edges=(edge,),
        )


def test_graph_rejects_edge_with_missing_target():
    node = AFRIPowerGraphNode(
        node_id="exec.001",
        node_type="Execution",
    )
    edge = AFRIPowerGraphEdge(
        source_id="exec.001",
        target_id="proof.001",
        relation="references",
    )

    with pytest.raises(AFRIPowerGraphModelError):
        AFRIPowerGraph(
            nodes=(node,),
            edges=(edge,),
        )


def test_graph_canonical_dict_preserves_boundary():
    graph = AFRIPowerGraph(
        nodes=(
            AFRIPowerGraphNode(
                node_id="exec.001",
                node_type="Execution",
            ),
            AFRIPowerGraphNode(
                node_id="proof.001",
                node_type="Proof",
            ),
        ),
        edges=(
            AFRIPowerGraphEdge(
                source_id="exec.001",
                target_id="proof.001",
                relation="references",
            ),
        ),
    )

    data = graph.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1


def test_build_graph_from_mappings():
    graph = build_graph_from_mappings(
        nodes=(
            {"node_id": "exec.001", "node_type": "Execution"},
            {"node_id": "proof.001", "node_type": "Proof"},
        ),
        edges=(
            {
                "source_id": "exec.001",
                "target_id": "proof.001",
                "relation": "references",
            },
        ),
    )

    assert isinstance(graph, AFRIPowerGraph)
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_build_graph_dict_from_mappings():
    data = build_graph_dict_from_mappings(
        nodes=(
            {"node_id": "exec.001", "node_type": "Execution"},
            {"node_id": "proof.001", "node_type": "Proof"},
        ),
        edges=(
            {
                "source_id": "exec.001",
                "target_id": "proof.001",
                "relation": "references",
            },
        ),
    )

    assert data["read_only"] is True
    assert data["creates_authority"] is False
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
