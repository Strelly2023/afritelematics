from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "afriride_system/mobile/driver_app/App.js"
PACKAGE = ROOT / "afriride_system/mobile/driver_app/package.json"
README = ROOT / "afriride_system/mobile/README.md"


def test_expo_phone_tester_signs_events_for_v1_ingestion():
    text = APP.read_text(encoding="utf-8")

    assert 'import CryptoJS from "crypto-js"' in text
    assert "/v1/events" in text
    assert "HmacSHA256" in text
    assert "stableStringify" in text
    assert "pilot-secret" in text
    assert "ostrinov_phone_001" in text


def test_expo_phone_tester_emits_day_one_driver_sequence():
    text = APP.read_text(encoding="utf-8")

    for event_type in (
        "DRIVER_ACCEPTED_RIDE",
        "TRIP_STARTED",
        "DRIVER_LOCATION_UPDATE",
        "TRIP_COMPLETED",
    ):
        assert event_type in text

    for label in ("Accept", "Start", "Location", "Complete", "Send Sequence", "Sync Pending"):
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
