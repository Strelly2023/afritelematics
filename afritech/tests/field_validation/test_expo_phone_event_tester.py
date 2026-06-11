from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "afriride_system/mobile/driver_app/App.js"
SHARED_CLIENT = ROOT / "afriride_system/mobile/shared/apiClient.js"
PACKAGE = ROOT / "afriride_system/mobile/driver_app/package.json"
README = ROOT / "afriride_system/mobile/README.md"


def test_expo_phone_tester_signs_events_for_v1_ingestion():
    text = SHARED_CLIENT.read_text(encoding="utf-8")

    assert "/auth/token" in text
    assert "client_event" in text
    assert "acceptRide({" in text
    assert "arriveRide({" in text
    assert "startTrip({" in text
    assert "completeTrip({" in text
    assert "setDriverStatus({" in text


def test_expo_phone_tester_emits_day_one_driver_sequence():
    text = APP.read_text(encoding="utf-8")

    for event_type in (
        "Accept",
        "Arrive",
        "Start",
        "Complete",
    ):
        assert event_type in text

    for label in ("Go online", "Go offline", "Accept", "Arrive", "Start", "Complete"):
        assert label in text


def test_expo_phone_tester_declares_crypto_dependency():
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))

    assert "crypto-js" in package["dependencies"]


def test_expo_phone_tester_readme_preserves_claim_boundary():
    text = README.read_text(encoding="utf-8")

    assert "signed phone-event tester" in text
    assert "http://<mac-lan-ip>:8000" in text
    assert "Do not use `localhost` from a physical phone." in text
    assert "candidate live pilot evidence" in text
    assert "does not certify pilot completion or production readiness" in text
