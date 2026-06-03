from __future__ import annotations

from afritech.afripower.graph.projection import (
    build_graph_projection_dict_from_mappings,
    projection_input_from_mapping,
)


def test_receipt_reference_type_normalizes_to_receipt():
    item = projection_input_from_mapping(
        {
            "receipt_id": "receipt.001",
            "receipt_type": "receipt_reference",
        }
    )

    assert item.artifact_id == "receipt.001"
    assert item.artifact_type == "Receipt"


def test_proof_reference_type_normalizes_to_proof():
    item = projection_input_from_mapping(
        {
            "proof_id": "proof.001",
            "proof_type": "proof_reference",
        }
    )

    assert item.artifact_id == "proof.001"
    assert item.artifact_type == "Proof"


def test_governance_traceability_is_supported_by_projection_payload():
    data = build_graph_projection_dict_from_mappings(
        (
            {
                "execution_id": "exec.001",
                "governance_traceability": [
                    {"type": "ADR", "id": "ADR-001"},
                    {"type": "RULE", "id": "RULE-001"},
                ],
            },
        )
    )

    assert data["read_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["projection_service"] == "afritech.afripower.graph.projection"
    assert "nodes" in data
    assert "edges" in data
  
