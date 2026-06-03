from __future__ import annotations

from afritech.security.event_authenticator import EventAuthenticator
from afritech.security.integrity_trace import IntegrityTrace


def test_detect_forged_event_timestamp() -> None:
    auth = EventAuthenticator()
    event = {
        "id": "e1",
        "timestamp": 1000,
        "payload": {"status": "requested"},
        "lineage": ("known-root",),
    }

    signature = auth.generate_signature(event, "secret")
    event["timestamp"] = 9999

    assert not auth.verify(event, signature, "secret")


def test_detect_forged_event_payload() -> None:
    auth = EventAuthenticator()
    event = {
        "id": "e1",
        "timestamp": 1000,
        "payload": {"status": "requested"},
        "lineage": ("known-root",),
    }

    signature = auth.generate_signature(event, "secret")
    event["payload"] = {"status": "completed"}

    assert not auth.verify(event, signature, "secret")


def test_integrity_trace_hash_is_stable_for_key_order() -> None:
    first = {"id": "e1", "timestamp": 1000, "payload": {"a": 1, "b": 2}}
    second = {"payload": {"b": 2, "a": 1}, "timestamp": 1000, "id": "e1"}

    assert IntegrityTrace.hash_event(first) == IntegrityTrace.hash_event(second)
