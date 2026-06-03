from __future__ import annotations

import pytest

from afritech.afripower.graph.projection import (
    AFRIPowerGraphProjectionError,
    AFRIPowerProjectionInput,
    build_graph_from_projection_inputs,
    build_graph_projection_dict_from_mappings,
    build_graph_projection_from_mappings,
    build_projection_graph,
    build_projection_graph_dict,
    projection_input_from_mapping,
)
# afritech/tests/afripower/test_graph_projection_service.py

def test_projection_input_accepts_valid_values():
    item = AFRIPowerProjectionInput(
        artifact_id="exec.001",
        artifact_type="Execution",
    )

    assert item.artifact_id == "exec.001"
    assert item.artifact_type == "Execution"


def test_projection_input_rejects_empty_artifact_id():
    with pytest.raises(AFRIPowerGraphProjectionError):
        AFRIPowerProjectionInput(
            artifact_id="",
            artifact_type="Execution",
        )


def test_projection_input_rejects_empty_artifact_type():
    with pytest.raises(AFRIPowerGraphProjectionError):
        AFRIPowerProjectionInput(
            artifact_id="exec.001",
            artifact_type="",
        )


def test_projection_input_canonical_dict_preserves_boundary():
    item = AFRIPowerProjectionInput(
        artifact_id="exec.001",
        artifact_type="Execution",
        references=(("Proof", "proof.001"),),
    )

    data = item.canonical_dict()

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False


def test_projection_input_from_mapping_uses_execution_id():
    item = projection_input_from_mapping(
        {
            "execution_id": "exec.001",
        }
    )

    assert item.artifact_id == "exec.001"
    assert item.artifact_type == "Execution"


def test_projection_input_from_mapping_uses_receipt_id():
    item = projection_input_from_mapping(
        {
            "receipt_id": "receipt.001",
            "receipt_type": "Receipt",
        }
    )

    assert item.artifact_id == "receipt.001"
    assert item.artifact_type == "Receipt"


def test_projection_input_from_mapping_uses_proof_id():
    item = projection_input_from_mapping(
        {
            "proof_id": "proof.001",
            "proof_type": "Proof",
        }
    )

    assert item.artifact_id == "proof.001"
    assert item.artifact_type == "Proof"


def test_projection_input_from_mapping_extracts_traceability():
    item = projection_input_from_mapping(
        {
            "execution_id": "exec.001",
            "traceability": [
                {"type": "Proof", "id": "proof.001"},
                {"type": "ADR", "id": "ADR-001"},
            ],
        }
    )

    assert item.references == (
        ("Proof", "proof.001"),
        ("ADR", "ADR-001"),
    )


def test_projection_input_from_mapping_extracts_references():
    item = projection_input_from_mapping(
        {
            "artifact_id": "exec.001",
            "artifact_type": "Execution",
            "references": [
                {"artifact_type": "Proof", "artifact_id": "proof.001"},
            ],
        }
    )

    assert item.references == (
        ("Proof", "proof.001"),
    )


def test_projection_input_from_mapping_ignores_bad_references():
    item = projection_input_from_mapping(
        {
            "execution_id": "exec.001",
            "traceability": [
                "bad",
                {"type": "Proof"},
                {"id": "proof.001"},
                {"type": "ADR", "id": "ADR-001"},
            ],
        }
    )

    assert item.references == (
        ("ADR", "ADR-001"),
    )


def test_projection_input_from_mapping_rejects_non_mapping():
    with pytest.raises(AFRIPowerGraphProjectionError):
        projection_input_from_mapping("bad")  # type: ignore[arg-type]


def test_build_graph_from_projection_inputs():
    graph = build_graph_from_projection_inputs(
        (
            AFRIPowerProjectionInput(
                artifact_id="exec.001",
                artifact_type="Execution",
                references=(("Proof", "proof.001"),),
            ),
        )
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_build_graph_from_projection_inputs_deduplicates_nodes_and_edges():
    graph = build_graph_from_projection_inputs(
        (
            AFRIPowerProjectionInput(
                artifact_id="exec.001",
                artifact_type="Execution",
                references=(
                    ("Proof", "proof.001"),
                    ("Proof", "proof.001"),
                ),
            ),
        )
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_build_graph_projection_from_mappings():
    graph = build_graph_projection_from_mappings(
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

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2


def test_build_graph_projection_dict_from_mappings_preserves_boundary():
    data = build_graph_projection_dict_from_mappings(
        (
            {
                "execution_id": "exec.001",
                "traceability": [
                    {"type": "Proof", "id": "proof.001"},
                ],
            },
        )
    )

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


def test_compatibility_alias_build_projection_graph():
    graph = build_projection_graph(
        (
            {
                "execution_id": "exec.001",
                "traceability": [
                    {"type": "Proof", "id": "proof.001"},
                ],
            },
        )
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_compatibility_alias_build_projection_graph_dict():
    data = build_projection_graph_dict(
        (
            {
                "execution_id": "exec.001",
                "traceability": [
                    {"type": "Proof", "id": "proof.001"},
                ],
            },
        )
    )

    assert data["read_only"] is True
    assert data["creates_authority"] is False
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1


def test_projection_output_is_deterministic():
    payloads = (
        {
            "execution_id": "exec.001",
            "traceability": [
                {"type": "Proof", "id": "proof.001"},
                {"type": "ADR", "id": "ADR-001"},
            ],
        },
    )

    first = build_graph_projection_dict_from_mappings(payloads)
    second = build_graph_projection_dict_from_mappings(payloads)

    assert first == second
