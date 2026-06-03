from __future__ import annotations

import pytest

from afritech.afripower.graph.models import (
    AFRIPowerGraphEdge,
    AFRIPowerGraphNode,
)
from afritech.afripower.graph.projection import (
    build_graph_projection_from_mappings,
)
from afritech.afripower.graph.query import query_graph
from afritech.afripower.graph.serializers import (
    AFRIPowerGraphSerializationError,
    ensure_serialized_graph_boundary,
    serialize_graph,
    serialize_graph_edge,
    serialize_graph_node,
    serialize_graph_summary,
    serialize_query_result,
)


def _sample_graph():
    return build_graph_projection_from_mappings(
        (
            {
                "execution_id": "exec.001",
                "traceability": [
                    {"type": "Proof", "id": "proof.001"},
                    {"type": "ADR", "id": "ADR-001"},
                ],
            },
        )
    )


def test_serialize_graph_node_preserves_boundary():
    node = AFRIPowerGraphNode(
        node_id="exec.001",
        node_type="Execution",
    )

    data = serialize_graph_node(node)

    assert data["node_id"] == "exec.001"
    assert data["node_type"] == "Execution"
    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_graph"] is False
    assert data["mutates_artifacts"] is False


def test_serialize_graph_node_rejects_wrong_type():
    with pytest.raises(AFRIPowerGraphSerializationError):
        serialize_graph_node("bad")  # type: ignore[arg-type]


def test_serialize_graph_edge_preserves_boundary():
    edge = AFRIPowerGraphEdge(
        source_id="exec.001",
        target_id="proof.001",
        relation="references",
    )

    data = serialize_graph_edge(edge)

    assert data["source_id"] == "exec.001"
    assert data["target_id"] == "proof.001"
    assert data["relation"] == "references"
    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_graph"] is False
    assert data["mutates_artifacts"] is False
    assert data["influences_runtime"] is False
    assert data["influences_replay"] is False
    assert data["influences_proof"] is False
    assert data["influences_ci"] is False
    assert data["influences_governance"] is False


def test_serialize_graph_edge_rejects_wrong_type():
    with pytest.raises(AFRIPowerGraphSerializationError):
        serialize_graph_edge("bad")  # type: ignore[arg-type]


def test_serialize_graph_preserves_boundary():
    graph = _sample_graph()

    data = serialize_graph(graph)

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_graph"] is False
    assert data["mutates_artifacts"] is False
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 2


def test_serialize_graph_rejects_wrong_type():
    with pytest.raises(AFRIPowerGraphSerializationError):
        serialize_graph("bad")  # type: ignore[arg-type]


def test_serialize_query_result_preserves_boundary():
    graph = _sample_graph()
    result = query_graph(graph, node_id="exec.001")

    data = serialize_query_result(result)

    assert data["query"] == "node_id:exec.001"
    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_graph"] is False
    assert data["mutates_artifacts"] is False
    assert len(data["nodes"]) == 1
    assert len(data["edges"]) == 2


def test_serialize_query_result_rejects_wrong_type():
    with pytest.raises(AFRIPowerGraphSerializationError):
        serialize_query_result("bad")  # type: ignore[arg-type]


def test_serialize_graph_summary():
    graph = _sample_graph()

    summary = serialize_graph_summary(graph)

    assert summary["node_count"] == 3
    assert summary["edge_count"] == 2
    assert summary["node_type_counts"] == {
        "ADR": 1,
        "Execution": 1,
        "Proof": 1,
    }
    assert summary["edge_relation_counts"] == {
        "references": 2,
    }
    assert summary["read_only"] is True
    assert summary["creates_authority"] is False


def test_serialize_graph_summary_rejects_wrong_type():
    with pytest.raises(AFRIPowerGraphSerializationError):
        serialize_graph_summary("bad")  # type: ignore[arg-type]


def test_ensure_serialized_graph_boundary_accepts_valid_payload():
    graph = _sample_graph()
    payload = serialize_graph(graph)

    ensure_serialized_graph_boundary(payload)


@pytest.mark.parametrize(
    "field",
    [
        "read_only",
        "reference_only",
        "display_only",
        "projection_only",
        "enterprise_intelligence_only",
    ],
)
def test_ensure_serialized_graph_boundary_rejects_required_true_field(field):
    graph = _sample_graph()
    payload = serialize_graph(graph)
    payload[field] = False

    with pytest.raises(AFRIPowerGraphSerializationError):
        ensure_serialized_graph_boundary(payload)


@pytest.mark.parametrize(
    "field",
    [
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
    ],
)
def test_ensure_serialized_graph_boundary_rejects_required_false_field(field):
    graph = _sample_graph()
    payload = serialize_graph(graph)
    payload[field] = True

    with pytest.raises(AFRIPowerGraphSerializationError):
        ensure_serialized_graph_boundary(payload)


def test_serialize_graph_is_deterministic():
    graph = _sample_graph()

    first = serialize_graph(graph)
    second = serialize_graph(graph)

    assert first == second
