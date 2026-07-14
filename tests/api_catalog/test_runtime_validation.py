from __future__ import annotations

import pytest

from afritech.api_catalog.enforcement import enforce_response_contract
from afritech.api_catalog.publication import response_envelope_schema
from afritech.api_catalog.runtime_validation import RuntimeContractViolation


def test_runtime_response_validation_passes_for_envelope() -> None:
    @enforce_response_contract(schema=response_envelope_schema(), operation_id="testOperation")
    def route() -> dict[str, object]:
        return {"data": {}, "meta": {"request_id": "req", "trace_id": "trace", "contract_version": "2026.07.0"}, "evidence": None, "errors": []}

    assert route()["errors"] == []


def test_runtime_response_drift_raises_violation() -> None:
    @enforce_response_contract(schema=response_envelope_schema(), operation_id="testOperation")
    def route() -> dict[str, object]:
        return {"unexpected": True}

    with pytest.raises(RuntimeContractViolation):
        route()
