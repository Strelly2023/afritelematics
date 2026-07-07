from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_required_apk_artifacts_and_checksums_exist() -> None:
    for name in [
        "novaride-rider-v2026.1.0-release.apk.sha256",
        "novaride-driver-v2026.1.0-release.apk.sha256",
        "novaride-operator-v2026.1.0-release.apk.sha256",
    ]:
        assert (ROOT / "apk" / name).is_file()


def test_novaride_icons_exist_for_all_apks() -> None:
    required_paths = [
        "rider_app/android/app/src/main/res/mipmap-mdpi/ic_launcher.png",
        "rider_app/android/app/src/main/res/mipmap-hdpi/ic_launcher.png",
        "rider_app/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png",
        "rider_app/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png",
        "rider_app/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
        "rider_app/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml",
        "rider_app/android/app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml",
        "driver_app/android/app/src/main/res/mipmap-mdpi/ic_launcher.png",
        "driver_app/android/app/src/main/res/mipmap-hdpi/ic_launcher.png",
        "driver_app/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png",
        "driver_app/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png",
        "driver_app/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
        "novaride_operator_app/android/app/src/main/res/mipmap-mdpi/ic_launcher.png",
        "novaride_operator_app/android/app/src/main/res/mipmap-hdpi/ic_launcher.png",
        "novaride_operator_app/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png",
        "novaride_operator_app/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png",
        "novaride_operator_app/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
    ]
    for path in required_paths:
        assert (ROOT / path).is_file()


def test_rider_tabs_and_actions_match_requirement_baseline() -> None:
    source = read("rider_app/App.tsx")
    for tab in ["Home", "Book Ride", "Trips", "Wallet", "Safety", "Receipts", "Profile"]:
        assert tab in source
    for button in [
        "Set pickup location",
        "Set destination",
        "Choose ride type",
        "Schedule ride",
        "Confirm pickup",
        "View nearby drivers",
        "Open safety center",
        "Open wallet",
        "Open promotions",
        "Select NovaRide Basic",
        "Add NovaPay wallet",
        "SOS",
        "Verify driver PIN",
        "Verify NovaID",
        "Logout",
    ]:
        assert button in source


def test_driver_tabs_and_actions_match_requirement_baseline() -> None:
    source = read("driver_app/App.tsx")
    for tab in ["Dashboard", "Requests", "Active Trip", "Earnings", "Vehicle", "Safety", "Profile"]:
        assert tab in source
    for marker in [
        "Go online",
        "Go offline",
        "Start shift",
        "End shift",
        "Accept ride",
        "Reject ride",
        "Arrived",
        "Start trip",
        "Verify rider PIN",
        "Withdraw to NovaPay",
        "Add vehicle",
        "SOS",
        "Verify NovaID",
        "Upload licence",
        "Manage NovaPay wallet",
    ]:
        assert marker.lower() in source.lower()


def test_operator_tabs_and_actions_match_requirement_baseline() -> None:
    source = read("novaride_operator_app/App.tsx")
    for tab in ["Overview", "Fleet", "Drivers", "Trips", "Earnings", "Compliance", "Support", "Settings"]:
        assert tab in source
    for button in [
        "View live fleet",
        "View active trips",
        "View alerts",
        "Export report",
        "Add vehicle",
        "Assign driver",
        "Approve driver",
        "Replay trip",
        "Reconcile payments",
        "Run compliance check",
        "Open incident",
        "Manage organization",
        "Manage NovaPay business wallet",
    ]:
        assert button.lower() in source.lower()
