from __future__ import annotations

from pathlib import Path

import yaml

from afritech.api.app import process
from afritech.storage.event_log import clear_event_log, get_all_events
from afritech.storage.replay_engine import replay_event


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_REGISTRY = ROOT / "afritech/architecture/implementation_registry.yaml"

MVP_IMPLEMENTATIONS = (
    "afritech.api.app",
    "afritech.execution.queue.simple_queue",
    "afritech.core.engine",
    "afritech.core.runtime.worker.worker",
    "afritech.storage.event_schema",
    "afritech.storage.event_log",
    "afritech.storage.replay_engine",
)


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_mvp_pipeline_implementations_are_registered() -> None:
    registry = load_yaml(IMPLEMENTATION_REGISTRY)
    implementations = registry["implementations"]

    for implementation in MVP_IMPLEMENTATIONS:
        entry = implementations[implementation]
        assert entry["implementation_state"] == "IMPLEMENTED"
        assert entry["ontology"] == "CANONICAL_MODULE_PATH"
        assert entry["semantic_properties"]["deterministic_execution"] is True
        assert entry["semantic_properties"]["replay_admissible"] is True
        assert entry["semantic_properties"]["proof_admissible"] is True
        assert entry["semantic_properties"]["replay_safe"] is True


def test_api_to_worker_to_replay_pipeline_is_consistent() -> None:
    clear_event_log()

    payload = {
        "request_id": "123",
        "user_id": "userA",
        "timestamp": 1700000000999,
        "action": "ride_request",
        "origin": "Melbourne CBD",
        "destination": "Melbourne Airport",
    }

    response = process(payload)

    assert response["status"] == "processed"
    assert response["request_id"] == "123"
    assert response["user_id"] == "userA"

    events = get_all_events()
    assert len(events) == 1

    event = events[0]
    assert event.request_id == "123"
    assert event.normalized_input["user_id"] == "userA"
    assert event.normalized_input["timestamp_bucket"] == 1700000000
    assert event.trace["stages"] == ["adapter", "normalization", "ingestion"]

    assert replay_event(event) == event.replay_hash


def test_api_pipeline_replay_hash_is_stable_for_payload_order() -> None:
    clear_event_log()

    first_payload = {
        "request_id": "stable",
        "user_id": "userA",
        "timestamp": 1700000000999,
        "origin": "CBD",
        "destination": "Airport",
    }
    second_payload = {
        "destination": "Airport",
        "origin": "CBD",
        "timestamp": 1700000000999,
        "user_id": "userA",
        "request_id": "stable",
    }

    first_response = process(first_payload)
    first_event = get_all_events()[-1]

    clear_event_log()

    second_response = process(second_payload)
    second_event = get_all_events()[-1]

    assert first_response["status"] == "processed"
    assert second_response["status"] == "processed"
    assert first_event.normalized_input == second_event.normalized_input
    assert first_event.replay_hash == second_event.replay_hash
