"""Tests for read-only governance impact query helpers."""

from __future__ import annotations

from afritech.impact.impact_query import (
    ADMISSIBILITY_AUTHORITY,
    DECISION_AUTHORITY,
    IMPACT_QUERY_STATUS,
    MUTATION_ALLOWED,
    QUERY_AUTHORITY,
    has_impact_reference,
    query_all_impacts,
    query_impact_payload,
    query_impact_records,
    query_impacted_executions,
)


def test_impact_query_flags_are_non_authoritative() -> None:
    assert IMPACT_QUERY_STATUS == "READ_ONLY_IMPACT_QUERY"

    assert QUERY_AUTHORITY is False
    assert DECISION_AUTHORITY is False
    assert ADMISSIBILITY_AUTHORITY is False
    assert MUTATION_ALLOWED is False


def test_query_impacted_executions() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0016"},
            ),
        },
        {
            "execution_id": "execution-002",
            "governance_traceability": (
                {"type": "RULE", "id": "RULE-016-4"},
            ),
        },
    )

    assert query_impacted_executions("ADR-0016", receipts) == (
        "execution-001",
    )
    assert query_impacted_executions("RULE-016-4", receipts) == (
        "execution-002",
    )


def test_query_impact_records() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0018"},
            ),
        },
    )

    records = query_impact_records("ADR-0018", receipts)

    assert len(records) == 1
    assert records[0].governance_id == "ADR-0018"
    assert records[0].execution_id == "execution-001"
    assert records[0].reference_type == "ADR"


def test_query_impact_payload_is_read_only() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0019"},
            ),
        },
    )

    payload = query_impact_payload("ADR-0019", receipts)

    assert payload["governance_id"] == "ADR-0019"
    assert payload["impacted_executions"] == ["execution-001"]

    assert payload["impact_query_status"] == "READ_ONLY_IMPACT_QUERY"
    assert payload["reference_only"] is True
    assert payload["read_only"] is True
    assert payload["display_only"] is True

    assert payload["query_authority"] is False
    assert payload["decision_authority"] is False
    assert payload["admissibility_authority"] is False
    assert payload["runtime_authority"] is False
    assert payload["governance_authority"] is False
    assert payload["mutation_allowed"] is False


def test_query_impact_payload_does_not_mutate_source_receipts() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0019"},
            ),
        },
    )

    original = tuple(
        {
            "execution_id": item["execution_id"],
            "governance_traceability": tuple(item["governance_traceability"]),
        }
        for item in receipts
    )

    query_impact_payload("ADR-0019", receipts)

    assert receipts == original


def test_query_all_impacts_groups_by_governance_id() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0016"},
                {"type": "RULE", "id": "RULE-016-4"},
            ),
        },
        {
            "execution_id": "execution-002",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0016"},
            ),
        },
    )

    payload = query_all_impacts(receipts)

    assert "ADR-0016" in payload["impacts"]
    assert "RULE-016-4" in payload["impacts"]

    assert len(payload["impacts"]["ADR-0016"]) == 2
    assert len(payload["impacts"]["RULE-016-4"]) == 1

    assert payload["runtime_authority"] is False
    assert payload["governance_authority"] is False
    assert payload["mutation_allowed"] is False


def test_query_all_impacts_is_display_only() -> None:
    payload = query_all_impacts(())

    assert payload["impact_query_status"] == "READ_ONLY_IMPACT_QUERY"
    assert payload["reference_only"] is True
    assert payload["read_only"] is True
    assert payload["display_only"] is True
    assert payload["query_authority"] is False
    assert payload["decision_authority"] is False
    assert payload["admissibility_authority"] is False
    assert payload["runtime_authority"] is False
    assert payload["governance_authority"] is False
    assert payload["mutation_allowed"] is False


def test_has_impact_reference() -> None:
    receipts = (
        {
            "execution_id": "execution-001",
            "governance_traceability": (
                {"type": "ADR", "id": "ADR-0016"},
            ),
        },
    )

    assert has_impact_reference("ADR-0016", receipts) is True
    assert has_impact_reference("ADR-9999", receipts) is False