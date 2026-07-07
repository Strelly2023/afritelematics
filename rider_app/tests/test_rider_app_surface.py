from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_novaride_rider_branding_and_android_identity() -> None:
    config = json.loads(read("app.json"))["expo"]
    gradle = read("android/app/build.gradle")
    strings = read("android/app/src/main/res/values/strings.xml")
    assert config["name"] == "NovaRide Rider"
    assert config["android"]["package"] == "com.novatech.novaride.rider"
    assert "com.novatech.novaride.rider" in gradle
    assert "NovaRide Rider" in strings


def test_rider_map_first_tabs_and_required_actions() -> None:
    app = read("App.tsx")
    for tab in ["Home", "Trips", "Safety", "Receipts", "Profile"]:
        assert tab in app
    for action in [
        "Request Ride", "Schedule", "Change Pickup", "Change Destination",
        "Choose Ride Type", "Confirm Fare", "Contact Driver", "Share Trip",
        "SOS", "Pay", "Rate Driver", "Open Dispute", "View Receipt", "View Replay",
    ]:
        assert f'label="{action}"' in app or action == "Choose Ride Type"
    assert "Live rides map" in app
    assert "onPress=" in app


def test_rider_booking_safety_payment_and_evidence_flows() -> None:
    app = read("App.tsx")
    for marker in [
        "choose pickup/dropoff", "review fare", "request ride", "match driver",
        "verify vehicle/driver", "NovaPay payment completed", "Digital proof receipt",
        "SOS active", "Operations notified", "Evidence frozen", "Replay package signed",
        "NovaID verified",
    ]:
        assert marker.lower() in app.lower()
    assert "useRideFlow" in app
    assert "submitRideRequest" in app
    assert "Ride request submitted" in app


def test_rider_accessibility_theme_and_offline_states() -> None:
    app = read("App.tsx")
    assert "accessibilityLabel" in app
    assert "accessibilityLiveRegion" in app
    assert "darkTheme" in app
    assert "low-bandwidth" in app.lower()
    assert '"offline"' in app
