from __future__ import annotations

import pytest

from afritech.afripower.projection_models import (
    AFRIPowerProjection,
    AFRIPowerProjectionEdge,
    AFRIPowerProjectionNode,
    build_afripower_projection,
    build_afripower_projection_dict,
    extract_traceability_references,
    normalize_node_type,
)


# =============================================================================
# NODE MODEL
# =============================================================================


def test_projection_node_accepts_valid_node_type():
    node = AFRIPowerProjectionNode(
        node_type="Execution",
        node_id="exec.demo.001",
    )

    assert node.node_type == "Execution"
    assert node.node_id == "exec.demo.001"


def test_projection_node_rejects_invalid_node_type():
    with pytest.raises(ValueError):
        AFRIPowerProjectionNode(
            node_type="InvalidType",
            node_id="node.001",
        )


def test_projection_node_rejects_empty_node_id():
    with pytest.raises(ValueError):
        AFRIPowerProjectionNode(
            node_type="Execution",
            node_id="",
        )


def test_projection_node_canonical_dict_is_read_only():
    node = AFRIPowerProjectionNode(
        node_type="Execution",
        node_id="exec.demo.001",
    )

    data = node.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["runtime_authority"] is False
    assert data["validation_authority"] is False
    assert data["governance_authority"] is False


def test_projection_node_uses_label_when_provided():
    node = AFRIPowerProjectionNode(
        node_type="Proof",
        node_id="proof.demo.001",
        label="Demo Proof",
    )

    assert node.canonical_dict()["label"] == "Demo Proof"


def test_projection_node_defaults_label_to_id():
    node = AFRIPowerProjectionNode(
        node_type="Proof",
        node_id="proof.demo.001",
    )

    assert node.canonical_dict()["label"] == "proof.demo.001"


# =============================================================================
# EDGE MODEL
# =============================================================================


def test_projection_edge_accepts_valid_relation():
    edge = AFRIPowerProjectionEdge(
        source_id="exec.demo.001",
        target_id="ADR-0001",
        relation="references",
    )

    assert edge.source_id == "exec.demo.001"
    assert edge.target_id == "ADR-0001"
    assert edge.relation == "references"


def test_projection_edge_rejects_empty_source_id():
    with pytest.raises(ValueError):
        AFRIPowerProjectionEdge(
            source_id="",
            target_id="ADR-0001",
            relation="references",
        )


def test_projection_edge_rejects_empty_target_id():
    with pytest.raises(ValueError):
        AFRIPowerProjectionEdge(
            source_id="exec.demo.001",
            target_id="",
            relation="references",
        )


def test_projection_edge_rejects_invalid_relation():
    with pytest.raises(ValueError):
        AFRIPowerProjectionEdge(
            source_id="exec.demo.001",
            target_id="ADR-0001",
            relation="executes",
        )


def test_projection_edge_canonical_dict_is_non_authoritative():
    edge = AFRIPowerProjectionEdge(
        source_id="exec.demo.001",
        target_id="ADR-0001",
        relation="references",
    )

    data = edge.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["creates_authority"] is False
    assert data["influences_runtime"] is False
    assert data["influences_replay"] is False
    assert data["influences_proof"] is False
    assert data["influences_ci"] is False
    assert data["influences_governance"] is False


# =============================================================================
# PROJECTION MODEL
# =============================================================================


def test_projection_canonical_dict_contains_nodes_and_edges():
    node = AFRIPowerProjectionNode(
        node_type="Execution",
        node_id="exec.demo.001",
    )
    edge = AFRIPowerProjectionEdge(
        source_id="exec.demo.001",
        target_id="ADR-0001",
        relation="references",
    )

    projection = AFRIPowerProjection(
        nodes=(node,),
        edges=(edge,),
    )

    data = projection.canonical_dict()

    assert len(data["nodes"]) == 1
    assert len(data["edges"]) == 1


def test_projection_canonical_dict_is_non_authoritative():
    projection = AFRIPowerProjection(
        nodes=(
            AFRIPowerProjectionNode(
                node_type="Execution",
                node_id="exec.demo.001",
            ),
        ),
        edges=tuple(),
    )

    data = projection.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["creates_authority"] is False
    assert data["runtime_authority"] is False
    assert data["validation_authority"] is False
    assert data["governance_authority"] is False


# =============================================================================
# NODE TYPE NORMALIZATION
# =============================================================================


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Enterprise", "Enterprise"),
        ("enterprise", "Enterprise"),
        ("CAPABILITY", "Capability"),
        ("workflow", "Workflow"),
        ("execution", "Execution"),
        ("adr", "ADR"),
        ("invariant", "Invariant"),
        ("rule", "Rule"),
        ("bind", "Binding"),
        ("binding", "Binding"),
        ("receipt", "Receipt"),
        ("proof", "Proof"),
        ("traceability", "Traceability"),
        ("explanation", "Explanation"),
        ("explainability", "Explanation"),
    ],
)
def test_normalize_node_type_known_values(raw: str, expected: str):
    assert normalize_node_type(raw) == expected


def test_normalize_node_type_unknown_value_preserved():
    assert normalize_node_type("CustomType") == "CustomType"


def test_normalize_node_type_empty_defaults_to_execution():
    assert normalize_node_type("") == "Execution"


def test_normalize_node_type_non_string_defaults_to_execution():
    assert normalize_node_type(None) == "Execution"


# =============================================================================
# TRACEABILITY EXTRACTION
# =============================================================================


def test_extract_traceability_references_from_valid_payload():
    payload = {
        "traceability": [
            {"type": "ADR", "id": "ADR-0001"},
            {"type": "Invariant", "id": "INVARIANT-001"},
        ]
    }

    refs = extract_traceability_references(payload)

    assert refs == (
        {"type": "ADR", "id": "ADR-0001"},
        {"type": "Invariant", "id": "INVARIANT-001"},
    )


def test_extract_traceability_references_normalizes_types():
    payload = {
        "traceability": [
            {"type": "adr", "id": "ADR-0001"},
            {"type": "proof", "id": "PROOF-001"},
        ]
    }

    refs = extract_traceability_references(payload)

    assert refs == (
        {"type": "ADR", "id": "ADR-0001"},
        {"type": "Proof", "id": "PROOF-001"},
    )


def test_extract_traceability_references_ignores_missing_type():
    payload = {
        "traceability": [
            {"id": "ADR-0001"},
        ]
    }

    assert extract_traceability_references(payload) == tuple()


def test_extract_traceability_references_ignores_missing_id():
    payload = {
        "traceability": [
            {"type": "ADR"},
        ]
    }

    assert extract_traceability_references(payload) == tuple()


def test_extract_traceability_references_ignores_non_mapping_items():
    payload = {
        "traceability": [
            "ADR-0001",
            123,
            None,
        ]
    }

    assert extract_traceability_references(payload) == tuple()


def test_extract_traceability_references_rejects_string_traceability():
    payload = {
        "traceability": "ADR-0001",
    }

    assert extract_traceability_references(payload) == tuple()


def test_extract_traceability_references_rejects_missing_traceability():
    assert extract_traceability_references({}) == tuple()


# =============================================================================
# PROJECTION BUILDER
# =============================================================================


def test_build_projection_creates_execution_node():
    projection = build_afripower_projection(
        [
            {
                "execution_id": "exec.demo.001",
                "traceability": [],
            }
        ]
    )

    assert len(projection.nodes) == 1
    assert projection.nodes[0].node_type == "Execution"
    assert projection.nodes[0].node_id == "exec.demo.001"


def test_build_projection_defaults_missing_execution_id():
    projection = build_afripower_projection(
        [
            {
                "traceability": [],
            }
        ]
    )

    assert projection.nodes[0].node_id == "unknown-execution"


def test_build_projection_creates_reference_nodes_and_edges():
    projection = build_afripower_projection(
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

    node_ids = {node.node_id for node in projection.nodes}
    edge_targets = {edge.target_id for edge in projection.edges}

    assert node_ids == {
        "exec.demo.001",
        "ADR-0001",
        "PROOF-001",
    }
    assert edge_targets == {
        "ADR-0001",
        "PROOF-001",
    }


def test_build_projection_deduplicates_nodes():
    projection = build_afripower_projection(
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

    node_ids = [node.node_id for node in projection.nodes]

    assert node_ids.count("ADR-0001") == 1


def test_build_projection_deduplicates_edges():
    projection = build_afripower_projection(
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

    assert len(projection.edges) == 1


def test_build_projection_preserves_multiple_payloads():
    projection = build_afripower_projection(
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

    node_ids = {node.node_id for node in projection.nodes}

    assert "exec.demo.001" in node_ids
    assert "exec.demo.002" in node_ids
    assert "ADR-0001" in node_ids
    assert "PROOF-001" in node_ids


def test_build_projection_dict_returns_dictionary():
    data = build_afripower_projection_dict(
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


def test_build_projection_dict_is_read_only():
    data = build_afripower_projection_dict(
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
    assert data["creates_authority"] is False


def test_build_projection_dict_contains_expected_node_count():
    data = build_afripower_projection_dict(
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

    assert len(data["nodes"]) == 3


def test_build_projection_dict_contains_expected_edge_count():
    data = build_afripower_projection_dict(
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

    assert len(data["edges"]) == 2
