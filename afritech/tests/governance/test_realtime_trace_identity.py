from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from afritech.api.realtime.ws_server import WebSocketHub
from afritech.security.device_identity import (
    DeviceIdentity,
    DeviceRegistry,
    PublicKeyAuthenticator,
)
from afritech.security.ed25519 import generate_keypair, sign_canonical_json
from afritech.trace.pilot_trace_recorder import PilotTraceRecorder
from afritech.trace.replay_inspector import ReplayInspector


class MemoryClient:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send_json(self, message: dict[str, Any]) -> None:
        self.messages.append(message)


class EchoReplayEngine:
    def execute(self, normalized_events):
        return tuple({"event_id": event["normalized_event_id"], "state": "applied"} for event in normalized_events)


def test_websocket_hub_is_projection_only_channel() -> None:
    hub = WebSocketHub()
    client = MemoryClient()
    hub.subscribe("ride-1", client)

    async def publish_state_update() -> dict[str, Any]:
        return await hub.publish_state_update(
            "ride-1",
            {"status": "DRIVER_EN_ROUTE", "driver_location": {"lat": -37.81, "lon": 144.96}},
        )

    message = asyncio.run(publish_state_update())

    assert hub.channel_for("ride-1") == "ride_ride-1"
    assert message["authority"] == "projection_only"
    assert message["sequence"] == 1
    assert client.messages == [message]


def test_pilot_trace_recorder_writes_hash_and_replay_inspector_verifies(tmp_path: Path) -> None:
    trace = {
        "trace_id": "trip_123",
        "events": [{"event_id": "evt-1"}],
        "normalized_events": [{"normalized_event_id": "norm-1"}],
        "execution_states": [{"event_id": "norm-1", "state": "applied"}],
        "witnesses": [{"witness_id": "wit-1"}],
    }
    recorder = PilotTraceRecorder(tmp_path)

    recorded = recorder.record(trace)
    loaded = recorder.load("trip_123")
    replayed = ReplayInspector().replay(loaded, EchoReplayEngine())

    assert recorded["hash"] == loaded["hash"]
    assert replayed == ({"event_id": "norm-1", "state": "applied"},)


def test_replay_inspector_rejects_mismatch() -> None:
    trace = {
        "trace_id": "trip_123",
        "normalized_events": [{"normalized_event_id": "norm-1"}],
        "execution_states": [{"event_id": "norm-1", "state": "different"}],
    }

    with pytest.raises(AssertionError, match="Replay mismatch"):
        ReplayInspector().replay(trace, EchoReplayEngine())


def test_device_identity_verifies_registered_public_key() -> None:
    private_key, public_key = generate_keypair()
    registry = DeviceRegistry()
    registry.register(
        DeviceIdentity(
            device_id="driver_45_phone_1",
            user_id="driver_45",
            public_key=public_key,
            registered_at=123456,
        )
    )
    event = {
        "event_id": "evt_123",
        "event_type": "DRIVER_ACCEPTED_RIDE",
        "device_id": "driver_45_phone_1",
        "entity_id": "ride_88",
        "timestamp": 123456,
        "logical_clock": 12,
        "payload": {"ride_id": "ride_88"},
    }
    signature = sign_canonical_json(
        {
            "device_id": event["device_id"],
            "entity_id": event["entity_id"],
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "logical_clock": event["logical_clock"],
            "payload": event["payload"],
            "timestamp": event["timestamp"],
        },
        private_key,
    )

    assert PublicKeyAuthenticator(registry).verify(event, signature)

    event["payload"] = {"ride_id": "ride_99"}
    assert not PublicKeyAuthenticator(registry).verify(event, signature)


def test_unregistered_device_is_rejected() -> None:
    registry = DeviceRegistry()
    event = {
        "event_id": "evt_123",
        "event_type": "DRIVER_ACCEPTED_RIDE",
        "device_id": "unknown",
        "entity_id": "ride_88",
        "timestamp": 123456,
        "logical_clock": 12,
        "payload": {"ride_id": "ride_88"},
    }

    with pytest.raises(ValueError, match="unregistered device"):
        PublicKeyAuthenticator(registry).verify(event, "00")
