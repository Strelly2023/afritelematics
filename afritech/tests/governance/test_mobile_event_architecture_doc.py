from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


DOC = (
    Path(__file__).resolve().parents[3]
    / "afritech/docs/operations/afriride_mobile_event_architecture.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def load_mobile_tests() -> dict[str, Any]:
    text = read_doc()
    match = re.search(r"```yaml\n(mobile_tests:.*?)\n```", text, re.DOTALL)
    assert match is not None
    payload = yaml.safe_load(match.group(1))
    assert isinstance(payload, dict)
    return payload["mobile_tests"]


def test_mobile_architecture_is_bounded_future_surface() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "STATUS: FUTURE PILOT IMPLEMENTATION SURFACE" in text
    assert "Mobile apps are not runtime truth" in text
    assert "does not claim that the Flutter apps are implemented" in text
    assert "mobile deployment readiness" in lowered


def test_mobile_architecture_preserves_constitutional_pipeline() -> None:
    text = read_doc()

    for stage in (
        "DRIVER / RIDER APP",
        "LOCAL EVENT BUFFER",
        "EDGE-COMPATIBLE EVENT FORMAT",
        "SYNC ENGINE",
        "EDGE ADAPTER",
        "NORMALIZATION",
        "ADMISSION",
        "EXECUTION",
        "WITNESS",
        "REPLAY",
    ):
        assert stage in text


def test_mobile_architecture_enforces_event_first_rule() -> None:
    text = read_doc()

    assert "UI action -> event -> local buffer -> sync -> edge adapter" in text
    assert "UI action -> direct API mutation" in text
    assert "mobile state -> runtime truth" in text
    assert "GPS reading -> core mutation" in text


def test_mobile_architecture_defines_core_modules() -> None:
    text = read_doc()

    for module in (
        "Event Store",
        "Replay-Safe Clock",
        "Sync Engine",
        "Network Client",
        "Client Security",
    ):
        assert module in text

    for rule in (
        "append-only pending event storage",
        "monotonic local counter",
        "same pending events -> same send order",
        "no parallel mutation sends",
        "sign canonical event content",
    ):
        assert rule in text


def test_mobile_architecture_defines_driver_and_rider_events() -> None:
    text = read_doc()

    for event_type in (
        "DRIVER_LOCATION_RECORDED",
        "DRIVER_ACCEPTED_RIDE",
        "TRIP_STARTED",
        "TRIP_COMPLETED",
        "RIDER_REQUESTED_RIDE",
        "RIDER_CANCELLED_RIDE",
        "RIDER_PAYMENT_TRIGGERED",
    ):
        assert event_type in text


def test_mobile_architecture_has_replay_safe_test_obligations() -> None:
    mobile_tests = load_mobile_tests()

    for test_name in (
        "offline_mode",
        "duplicate_sends",
        "reordering",
        "crash_recovery",
        "tamper_attempt",
    ):
        assert test_name in mobile_tests
        assert mobile_tests[test_name]["verifies"]
