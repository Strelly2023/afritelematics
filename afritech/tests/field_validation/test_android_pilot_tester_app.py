from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

DRIVER_APP_MAIN = ROOT / "afriride_system/flutter/driver_app/lib/main.dart"

PILOT_CONTROLLER = (
    ROOT / "afriride_system/flutter/driver_app/lib/driver/driver_controller.dart"
)

PILOT_GUIDE = (
    ROOT / "afriride_system/flutter/driver_app/ANDROID_PILOT_TEST.md"
)


def test_driver_app_main_is_verified_runnable_shell():
    text = DRIVER_APP_MAIN.read_text(encoding="utf-8")

    assert "AfriRide Driver" in text
    assert "AfriRideDriverApp" in text
    assert "DriverHomeShell" in text
    assert "AfriRideApiClient" in text

    for required_surface in (
        "RideRequestsScreen",
        "TripLifecycleScreen",
        "ReplayScreen",
        "EarningsScreen",
    ):
        assert required_surface in text

    for navigation_label in (
        "Requests",
        "Trip",
        "Replay",
        "Earnings",
    ):
        assert navigation_label in text


def test_driver_app_main_preserves_authority_boundary():
    text = DRIVER_APP_MAIN.read_text(encoding="utf-8")

    assert "compute pricing" in text
    assert "assign drivers" in text
    assert "rank rides" in text
    assert "mutate replay" in text
    assert "generate receipts" in text
    assert "authorize payouts" in text
    assert "Server-side systems remain the authority" in text


def test_device_backed_pilot_controller_emits_required_driver_events():
    controller = PILOT_CONTROLLER.read_text(encoding="utf-8")

    for required in (
        "acceptRide",
        "startTrip",
        "recordLocation",
        "completeTrip",
        "syncPending",
    ):
        assert required in controller

    for event_type in (
        "DRIVER_ACCEPTED_RIDE",
        "TRIP_STARTED",
        "DRIVER_LOCATION_UPDATE",
        "TRIP_COMPLETED",
    ):
        assert event_type in controller


def test_android_pilot_tester_preserves_claim_boundary():
    guide = PILOT_GUIDE.read_text(encoding="utf-8")

    assert "DEVICE-BACKED REHEARSAL TOOL" in guide
    assert "does not define replay truth" in guide
    assert "candidate live pilot evidence" in guide
    assert "device-backed rehearsal" in guide

    for forbidden in (
        "pilot completed",
        "production ready",
        "public launch ready",
        "regulatory approved",
        "market validated",
    ):
        assert forbidden in guide


def test_android_pilot_tester_documents_phone_network_rule():
    guide = PILOT_GUIDE.read_text(encoding="utf-8")

    assert "http://<mac-lan-ip>:8000" in guide
    assert "not:" in guide
    assert "http://localhost:8000" in guide