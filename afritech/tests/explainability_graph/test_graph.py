"""Tests for the read-only Explainability Graph builder."""

from __future__ import annotations

from afritech.explainability_graph.graph import (
    build_explainability_graph,
    build_explainability_graph_dict,
    build_graph_from_explanation,
    build_graph_from_receipt,
)


def test_graph_builds_from_traceability_payload() -> None:
    payload = {
        "execution_id": "execution-001",
        "governance_traceability": [
            {"type": "ADR", "id": "ADR-0016"},
            {"type": "RULE", "id": "RULE-016-4"},
            {"type": "INVARIANT", "id": "INVARIANT-016"},
            {"type": "BINDING", "id": "BIND-016"},
        ],
    }

    graph = build_explainability_graph_dict(payload)

    assert graph["read_only"] is True
    assert graph["display_only"] is True
    assert graph["non_authoritative"] is True

    assert graph["runtime_authority"] is False
    assert graph["validation_authority"] is False

    assert graph["influences_runtime"] is False
    assert graph["influences_replay"] is False
    assert graph["influences_proof"] is False

    assert len(graph["nodes"]) == 5
    assert len(graph["edges"]) == 4


def test_graph_normalizes_governance_node_types() -> None:
    payload = {
        "execution_id": "execution-001",
        "governance_traceability": [
            {"type": "RULE", "id": "RULE-016-4"},
            {"type": "INVARIANT", "id": "INVARIANT-016"},
            {"type": "BINDING", "id": "BIND-016"},
        ],
    }

    graph = build_explainability_graph_dict(payload)

    node_types = {node["type"] for node in graph["nodes"]}

    assert "Execution" in node_types
    assert "Rule" in node_types
    assert "Invariant" in node_types
    assert "Binding" in node_types


def test_graph_does_not_mutate_input_payload() -> None:
    payload = {
        "execution_id": "execution-001",
        "governance_traceability": [
            {"type": "ADR", "id": "ADR-0016"},
        ],
    }

    build_explainability_graph_dict(payload)

    assert payload == {
        "execution_id": "execution-001",
        "governance_traceability": [
            {"type": "ADR", "id": "ADR-0016"},
        ],
    }


def test_graph_ignores_malformed_references() -> None:
    payload = {
        "execution_id": "execution-001",
        "governance_traceability": [
            {"type": "ADR", "id": "ADR-0016"},
            {"type": "RULE"},
            {"id": "INVARIANT-016"},
            "bad-reference",
            None,
        ],
    }

    graph = build_explainability_graph_dict(payload)

    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1


def test_graph_defaults_unknown_execution_id() -> None:
    graph = build_explainability_graph_dict(
        {
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0016"},
            ]
        }
    )

    assert graph["nodes"][0]["type"] == "Execution"
    assert graph["nodes"][0]["id"] == "unknown-execution"


def test_graph_compatibility_helpers_match() -> None:
    payload = {
        "execution_id": "execution-001",
        "governance_traceability": [
            {"type": "ADR", "id": "ADR-0016"},
        ],
    }

    assert build_graph_from_receipt(payload) == build_explainability_graph_dict(
        payload
    )

    assert build_graph_from_explanation(
        payload
    ) == build_explainability_graph_dict(payload)


def test_graph_object_canonical_dict() -> None:
    payload = {
        "execution_id": "execution-001",
        "governance_traceability": [
            {"type": "ADR", "id": "ADR-0016"},
        ],
    }

    graph = build_explainability_graph(payload)
    canonical = graph.canonical_dict()

    assert canonical["nodes"][0]["type"] == "Execution"
    assert canonical["edges"][0]["relation"] == "governed_by"