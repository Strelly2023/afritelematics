"""Tests for read-only governance impact index."""

from __future__ import annotations

from afritech.impact.impact_index import (
    CI_AUTHORITY,
    DISPLAY_ONLY,
    ENFORCEMENT_AUTHORITY,
    GOVERNANCE_AUTHORITY,
    IMPACT_INDEX_STATUS,
    MUTATION_ALLOWED,
    PROOF_AUTHORITY,
    PROJECTION_DEPENDENCY,
    READ_ONLY,
    RECEIPT_MUTATION_ALLOWED,
    REFERENCE_ONLY,
    REPLAY_AUTHORITY,
    RUNTIME_AUTHORITY,
    RUNTIME_DEPENDENCY,
    VALIDATION_AUTHORITY,
    ImpactRecord,
    build_impact_index,
    impacted_executions_for_governance,
    impact_payload_for_governance,
)


def test_impact_index_flags_are_non_authoritative() -> None:
    assert IMPACT_INDEX_STATUS == "READ_ONLY_IMPACT_INDEX"

    assert REFERENCE_ONLY is True
    assert READ_ONLY is True
    assert DISPLAY_ONLY is True

    assert RUNTIME_AUTHORITY is False
    assert ENFORCEMENT_AUTHORITY is False
    assert VALIDATION_AUTHORITY is False
    assert REPLAY_AUTHORITY is False
    assert PROOF_AUTHORITY is False
    assert CI_AUTHORITY is False
    assert GOVERNANCE_AUTHORITY is False

    assert RUNTIME_DEPENDENCY is False
    assert PROJECTION_DEPENDENCY is False
    assert MUTATION_ALLOWED is False
    assert RECEIPT_MUTATION_ALLOWED is False


def test_impact_record_canonical_dict_is_reference_only() -> None:
    record = ImpactRecord(
        governance_id="ADR-0016",
        execution_id="execution-001",
        reference_type="ADR",
    )

    payload = record.canonical_dict()

    assert payload["governance_id"] == "ADR-0016"
    assert payload["execution_id"] == "execution-001"
    assert payload["reference_type"] == "ADR"

    assert payload["impact_index_status"] == "READ_ONLY_IMPACT_INDEX"
    assert payload["reference_only"] is True
    assert payload["read_only"] is True
    assert payload["display_only"] is True
    assert payload["runtime_authority"] is False
    assert payload["validation_authority"] is False
    assert payload["governance_authority"] is False


def test_build_impact_index_from_receipts() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0016"},
                {"type": "RULE", "id": "RULE-016-4"},
            ],
        },
        {
            "execution_id": "execution-002",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0016"},
            ],
        },
    )

    index = build_impact_index(receipts)

    assert index.impacted_executions("ADR-0016") == (
        "execution-001",
        "execution-002",
    )

    assert index.impacted_executions("RULE-016-4") == (
        "execution-001",
    )


def test_impact_index_payload_for_governance() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0018"},
            ],
        },
    )

    payload = impact_payload_for_governance("ADR-0018", receipts)

    assert payload["governance_id"] == "ADR-0018"
    assert payload["impacted_executions"] == ["execution-001"]
    assert payload["reference_only"] is True
    assert payload["read_only"] is True
    assert payload["display_only"] is True
    assert payload["runtime_authority"] is False
    assert payload["validation_authority"] is False
    assert payload["governance_authority"] is False


def test_impacted_executions_for_governance_helper() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": [
                {"type": "BINDING", "id": "BIND-019"},
            ],
        },
        {
            "execution_id": "execution-002",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0019"},
            ],
        },
    )

    assert impacted_executions_for_governance(
        "BIND-019",
        receipts,
    ) == ("execution-001",)


def test_impact_index_ignores_malformed_receipts() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0016"},
                {"type": "RULE"},
                {"id": ""},
                "bad-reference",
            ],
        },
        {
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-0018"},
            ],
        },
    )

    index = build_impact_index(receipts)

    assert index.impacted_executions("ADR-0016") == ("execution-001",)
    assert index.impacted_executions("ADR-0018") == ()