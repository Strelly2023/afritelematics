from __future__ import annotations

import pytest

from afritech.afripower.graph_projection import (
    AFRIPowerEdge,
    AFRIPowerKnowledgeGraph,
    AFRIPowerNode,
    build_afripower_knowledge_graph,
    build_afripower_knowledge_graph_dict,
    build_graph_projection,
)


# =============================================================================
# NODE MODEL
# =============================================================================


def test_graph_node_accepts_valid_type():
    node = AFRIPowerNode(
        node_type="Execution",
        node_id="exec.demo.001",
    )

    assert node.node_type == "Execution"
    assert node.node_id == "exec.demo.001"


def test_graph_node_rejects_invalid_type():
    with pytest.raises(ValueError):
        AFRIPowerNode(
            node_type="InvalidType",
            node_id="node.demo.001",
        )


def test_graph_node_rejects_empty_id():
    with pytest.raises(ValueError):
        AFRIPowerNode(
            node_type="Execution",
            node_id="",
        )


def test_graph_node_canonical_dict_is_read_only():
    node = AFRIPowerNode(
        node_type="Execution",
        node_id="exec.demo.001",
    )

    data = node.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["runtime_authority"] is False
    assert data["validation_authority"] is False
    assert data["governance_authority"] is False


def test_graph_node_label_defaults_to_node_id():
    node = AFRIPowerNode(
        node_type="Proof",
        node_id="PROOF-001",
    )

    assert node.canonical_dict()["label"] == "PROOF-001"


def test_graph_node_accepts_custom_label():
    node = AFRIPowerNode(
        node_type="Proof",
        node_id="PROOF-001",
        label="Replay Proof",
    )

    assert node.canonical_dict()["label"] == "Replay Proof"


# =============================================================================
# EDGE MODEL
# =============================================================================


def test_graph_edge_accepts_valid_relation():
    edge = AFRIPowerEdge(
        source_id="exec.demo.001",
        target_id="ADR-0001",
        relation="references",
    )

    assert edge.source_id == "exec.demo.001"
    assert edge.target_id == "ADR-0001"
    assert edge.relation == "references"


def test_graph_edge_rejects_empty_source_id():
    with pytest.raises(ValueError):
        AFRIPowerEdge(
            source_id="",
            target_id="ADR-0001",
            relation="references",
        )


def test_graph_edge_rejects_empty_target_id():
    with pytest.raises(ValueError):
        AFRIPowerEdge(
            source_id="exec.demo.001",
            target_id="",
            relation="references",
        )


def test_graph_edge_rejects_invalid_relation():
    with pytest.raises(ValueError):
        AFRIPowerEdge(
            source_id="exec.demo.001",
            target_id="ADR-0001",
            relation="executes",
        )


def test_graph_edge_canonical_dict_is_non_authoritative():
    edge = AFRIPowerEdge(
        source_id="exec.demo.001",
        target_id="ADR-0001",
        relation="references",
    )

    data = edge.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["influences_runtime"] is False
    assert data["influences_replay"] is False
    assert data["influences_proof"] is False
    assert data["influences_ci"] is False
    assert data["influences_governance"] is False


# =============================================================================
# KNOWLEDGE GRAPH MODEL
# =============================================================================


def test_knowledge_graph_canonical_dict_contains_nodes_and_edges():
    node = AFRIPowerNode(
        node_type="Execution",
        node_id="exec.demo.001",
    )
    edge = AFRIPowerEdge(
        source_id="exec.demo.001",
        target_id="ADR-0001",
        relation="references",
    )

    graph = AFRIPowerKnowledgeGraph(
        nodes=(node,),
        edges=(edge,),
    )

    data = graph.canonical_dict()

    assert len(data["nodes"]) == 1
    assert len(data["edges"]) == 1


def test_knowledge_graph_canonical_dict_preserves_boundary():
    graph = AFRIPowerKnowledgeGraph(
        nodes=(
            AFRIPowerNode(
                node_type="Execution",
                node_id="exec.demo.001",
            ),
        ),
        edges=tuple(),
    )

    data = graph.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["cannot_create_authority"] is True
    assert data["runtime_authority"] is False
    assert data["validation_authority"] is False
    assert data["governance_authority"] is False


# =============================================================================
# GRAPH BUILDER
# =============================================================================


def test_build_knowledge_graph_creates_execution_node():
    graph = build_afripower_knowledge_graph(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [],
            }
        ]
    )

    assert len(graph.nodes) == 1
    assert graph.nodes[0].node_type == "Execution"
    assert graph.nodes[0].node_id == "exec.demo.001"


def test_build_knowledge_graph_defaults_missing_execution_id():
    graph = build_afripower_knowledge_graph(
        [
            {
                "traceability": [],
            }
        ]
    )

    assert len(graph.nodes) == 1
    assert graph.nodes[0].node_id == "unknown-execution"


def test_build_knowledge_graph_creates_referenced_nodes():
    graph = build_afripower_knowledge_graph(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "ADR", "id": "ADR-0001"},
                    {"type": "Proof", "id": "PROOF-001"},
                    {"type": "Invariant", "id": "INVARIANT-001"},
                ],
            }
        ]
    )

    node_ids = {node.node_id for node in graph.nodes}

    assert node_ids == {
        "exec.demo.001",
        "ADR-0001",
        "PROOF-001",
        "INVARIANT-001",
    }


def test_build_knowledge_graph_creates_reference_edges():
    graph = build_afripower_knowledge_graph(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "ADR", "id": "ADR-0001"},
                    {"type": "Proof", "id": "PROOF-001"},
                ],
            }
        ]
    )

    assert len(graph.edges) == 2
    assert all(edge.relation == "references" for edge in graph.edges)


def test_build_knowledge_graph_deduplicates_nodes():
    graph = build_afripower_knowledge_graph(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "ADR", "id": "ADR-0001"},
                    {"type": "ADR", "id": "ADR-0001"},
                ],
            }
        ]
    )

    node_ids = [node.node_id for node in graph.nodes]

    assert node_ids.count("ADR-0001") == 1


def test_build_knowledge_graph_deduplicates_edges():
    graph = build_afripower_knowledge_graph(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "ADR", "id": "ADR-0001"},
                    {"type": "ADR", "id": "ADR-0001"},
                ],
            }
        ]
    )

    assert len(graph.edges) == 1


def test_build_knowledge_graph_handles_multiple_payloads():
    graph = build_afripower_knowledge_graph(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "ADR", "id": "ADR-0001"},
                ],
            },
            {
                "execution_id": "exec.demo.002",
                "traceability": [
                    {"type": "Proof", "id": "PROOF-001"},
                ],
            },
        ]
    )

    node_ids = {node.node_id for node in graph.nodes}

    assert "exec.demo.001" in node_ids
    assert "exec.demo.002" in node_ids
    assert "ADR-0001" in node_ids
    assert "PROOF-001" in node_ids


def test_build_knowledge_graph_ignores_bad_traceability_items():
    graph = build_afripower_knowledge_graph(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    "ADR-0001",
                    {"type": "ADR"},
                    {"id": "ADR-0002"},
                    {"type": "Proof", "id": "PROOF-001"},
                ],
            }
        ]
    )

    node_ids = {node.node_id for node in graph.nodes}

    assert "exec.demo.001" in node_ids
    assert "PROOF-001" in node_ids
    assert "ADR-0001" not in node_ids
    assert "ADR-0002" not in node_ids


# =============================================================================
# DICT BUILDERS
# =============================================================================


def test_build_knowledge_graph_dict_returns_dictionary():
    data = build_afripower_knowledge_graph_dict(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [],
            }
        ]
    )

    assert isinstance(data, dict)


def test_build_knowledge_graph_dict_preserves_boundary():
    data = build_afripower_knowledge_graph_dict(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "ADR", "id": "ADR-0001"},
                ],
            }
        ]
    )

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["runtime_authority"] is False
    assert data["validation_authority"] is False
    assert data["governance_authority"] is False


def test_build_knowledge_graph_dict_contains_expected_counts():
    data = build_afripower_knowledge_graph_dict(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "ADR", "id": "ADR-0001"},
                    {"type": "Invariant", "id": "INVARIANT-001"},
                    {"type": "Proof", "id": "PROOF-001"},
                ],
            }
        ]
    )

    assert len(data["nodes"]) == 4
    assert len(data["edges"]) == 3


def test_build_graph_projection_compatibility_helper():
    data = build_graph_projection(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "ADR", "id": "ADR-0001"},
                ],
            }
        ]
    )

    assert isinstance(data, dict)
    assert data["read_only"] is True
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1


def test_build_graph_projection_never_creates_authority():
    data = build_graph_projection(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [
                    {"type": "Proof", "id": "PROOF-001"},
                ],
            }
        ]
    )

    assert data["creates_authority"] is False
    assert data["runtime_authority"] is False
    assert data["validation_authority"] is False
    assert data["governance_authority"] is False


def test_build_graph_projection_is_deterministic_for_same_input():
    payloads = [
        {
            "execution_id": "exec.demo.001",
            "traceability": [
                {"type": "ADR", "id": "ADR-0001"},
                {"type": "Proof", "id": "PROOF-001"},
            ],
        }
    ]

    first = build_graph_projection(payloads)
    second = build_graph_projection(payloads)

    assert first == second
