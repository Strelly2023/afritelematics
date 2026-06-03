from __future__ import annotations

from afritech.afripower.dashboard.services import build_dashboard_payload


def _build_sample_receipts():
    return (
        {
            "execution_id": "exec-1",
            "governance_traceability": [
                {"type": "ADR", "id": "ADR-1"},
                {"type": "RULE", "id": "RULE-1"},
            ],
        },
    )


def test_dashboard_executes():
    payload = build_dashboard_payload(({"execution_id": "exec-1"},))

    assert payload["read_only"] is True
    assert payload["authoritative"] is False
    assert payload["observational_only"] is True
    assert "dashboard_status" in payload


def test_dashboard_structure():
    payload = build_dashboard_payload(_build_sample_receipts())

    assert isinstance(payload, dict)
    assert "read_only" in payload
    assert "observational_only" in payload
    assert "authoritative" in payload
    assert "dashboard_status" in payload


def test_dashboard_is_deterministic():
    receipts = _build_sample_receipts()

    assert build_dashboard_payload(receipts) == build_dashboard_payload(receipts)


def test_dashboard_empty_input():
    payload = build_dashboard_payload(())

    assert isinstance(payload, dict)
    assert payload["read_only"] is True
    assert payload["authoritative"] is False
    assert payload["observational_only"] is True
    assert "dashboard_status" in payload


def test_dashboard_multiple_receipts():
    receipts = (
        {
            "execution_id": "exec-1",
            "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
        },
        {
            "execution_id": "exec-2",
            "governance_traceability": [{"type": "RULE", "id": "RULE-1"}],
        },
    )

    payload = build_dashboard_payload(receipts)

    assert isinstance(payload, dict)
    assert payload["read_only"] is True
    assert payload["authoritative"] is False


def test_dashboard_flags_are_stable():
    payload = build_dashboard_payload(_build_sample_receipts())

    assert payload["read_only"] is True
    assert payload["observational_only"] is True
    assert payload["authoritative"] is False


def test_dashboard_handles_missing_traceability():
    payload = build_dashboard_payload(({"execution_id": "exec-1"},))

    assert isinstance(payload, dict)
    assert payload["read_only"] is True
    assert payload["authoritative"] is False
    assert payload["observational_only"] is True
