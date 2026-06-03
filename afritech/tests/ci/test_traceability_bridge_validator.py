from afritech.ci.traceability_bridge_validator import validate
from afritech.traceability.receipt_links import attach_traceability
from afritech.traceability.references import GovernanceReference


def test_traceability_bridge_validator_passes():
    validate()


def test_traceability_bridge_adds_reference_metadata_without_mutating_receipt():
    receipt = {
        "receipt_id": "abc123",
        "result": "SUCCESS",
        "execution_hash": "xyz789",
    }
    refs = [
        GovernanceReference("ADR", "ADR-0016"),
        GovernanceReference("RULE", "RULE-016-4"),
    ]

    enriched = attach_traceability(receipt, refs)

    assert "governance_traceability" not in receipt
    assert enriched is not receipt
    assert enriched["receipt_id"] == "abc123"
    assert enriched["governance_traceability"] == [
        {"type": "ADR", "id": "ADR-0016"},
        {"type": "RULE", "id": "RULE-016-4"},
    ]
    assert enriched["traceability_bridge"] == {
        "status": "REFERENCE_ONLY",
        "reference_only": True,
        "runtime_authority": False,
        "enforcement_authority": False,
        "projection_dependency": False,
    }
