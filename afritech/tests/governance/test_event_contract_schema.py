from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from afritech.api.contracts.rules import EventContractRules
from afritech.api.contracts.validator import EventContractValidator
from afritech.api.ingestion.event_ingestion import MobileEventAuthenticator
from afritech.api.ingestion.event_ingestion_with_contract import EventIngestionPipeline


ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "afritech/api/contracts"
SECRET = "pilot-secret"


def make_valid_event(
    *,
    event_id: str = "e1",
    logical_clock: int = 1,
    event_type: str = "TRIP_STARTED",
) -> dict[str, object]:
    event = {
        "event_id": event_id,
        "event_type": event_type,
        "device_id": "d1",
        "entity_id": "ride_1",
        "timestamp": 1,
        "logical_clock": logical_clock,
        "payload": {},
        "signature": "0" * 64,
    }
    event["signature"] = MobileEventAuthenticator().generate_signature(event, SECRET)
    return event


def test_event_schema_fields() -> None:
    validator = EventContractValidator()

    validator.validate_event(make_valid_event())


def test_invalid_event_type() -> None:
    validator = EventContractValidator()
    bad_event = make_valid_event(event_type="INVALID")

    with pytest.raises(ValidationError):
        validator.validate_event(bad_event)


def test_event_batch_schema_rejects_empty_batch() -> None:
    validator = EventContractValidator()

    with pytest.raises(ValidationError):
        validator.validate_batch({"events": []})


def test_schema_forbids_extra_fields() -> None:
    validator = EventContractValidator()
    event = make_valid_event()
    event["direct_mutation"] = True

    with pytest.raises(ValidationError):
        validator.validate_event(event)


def test_logical_clock_monotonic() -> None:
    rules = EventContractRules()

    e1 = {"event_id": "e1", "device_id": "d1", "logical_clock": 1, "payload": {}}
    e2 = {"event_id": "e2", "device_id": "d1", "logical_clock": 1, "payload": {}}

    rules.validate(e1)

    with pytest.raises(ValueError, match="logical_clock_regression"):
        rules.validate(e2)


def test_contract_pipeline_rejects_duplicate_event() -> None:
    pipeline = EventIngestionPipeline(SECRET)
    event = make_valid_event()

    result = pipeline.ingest({"events": [event, event]})

    assert len(result["accepted"]) == 1
    assert result["rejected"] == [{"event_id": "e1", "reason": "duplicate_event"}]


def test_contract_schema_files_are_canonical_json_objects() -> None:
    for filename in ("event.schema.json", "event_batch.schema.json"):
        payload = json.loads((CONTRACTS / filename).read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        assert payload["additionalProperties"] is False
