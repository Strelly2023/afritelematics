from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
APPS = {
    "rider_app": ("NovaRide Rider", "com.novatech.novaride.rider", ["Home", "Trips", "Safety", "Receipts", "Profile"]),
    "driver_app": ("NovaRide Driver", "com.novatech.novaride.driver", ["home", "requests", "trip", "earnings", "profile"]),
    "novaride_operator_app": ("NovaRide Operator", "com.novatech.novaride.operator", ["City", "Rides", "Dispatch", "Safety", "Evidence"]),
    "novaride_fleet_app": ("NovaRide Fleet", "com.novatech.novaride.fleet", ["Fleet", "Vehicles", "Drivers", "Maintenance", "Reports"]),
}
PACKAGES = [
    "novaride-core", "novaride-ui", "novaride-dispatch-sdk", "novaride-safety-sdk",
    "novaride-pricing-sdk", "novaride-maps-sdk", "novaride-evidence-sdk",
    "novaride-earnings-sdk", "novaride-support-sdk",
]
PORTALS = [
    "novaride_operations_portal", "novaride_dispatch_portal", "novaride_support_console",
    "novaride_compliance_portal", "novaride_fleet_portal", "novaride_partner_portal",
]


@pytest.mark.parametrize(("directory", "contract"), APPS.items())
def test_app_package_name_and_tabs(directory: str, contract: tuple[str, str, list[str]]) -> None:
    name, package_id, tabs = contract
    app = ROOT / directory
    config = json.loads((app / "app.json").read_text())["expo"]
    gradle = (app / "android/app/build.gradle").read_text()
    source = (app / "App.tsx").read_text()
    assert config["name"] == name
    assert config["android"]["package"] == package_id
    assert f"applicationId '{package_id}'" in gradle
    for tab in tabs:
        assert tab in source


def test_rider_buttons_are_wired() -> None:
    source = (ROOT / "rider_app/App.tsx").read_text()
    for button in [
        "Request Ride", "Schedule", "Change Pickup", "Change Destination", "Confirm Fare",
        "Contact Driver", "Share Trip", "SOS", "Pay", "Rate Driver", "Open Dispute",
        "View Receipt", "View Replay",
    ]:
        assert f'label="{button}"' in source
    assert "onPress={onPress}" in source


def test_driver_buttons_and_lifecycle_are_wired() -> None:
    app = (ROOT / "driver_app/App.tsx").read_text()
    combined = app + "\n" + "\n".join(path.read_text() for path in (ROOT / "driver_app/ui/screens").glob("*.tsx"))
    for action in [
        "Go Online", "Go Offline", "Accept", "Reject", "Navigate", "Arrived",
        "Start Trip", "Complete Trip", "SOS", "Earnings", "Payout", "Proof", "Support",
    ]:
        assert action.lower() in combined.lower()
    assert "onAccept" in combined and "onReject" in combined
    assert "onArrived" in combined and "onStart" in combined and "onComplete" in combined


def test_operator_and_fleet_actions_are_wired() -> None:
    for directory in ("novaride_operator_app", "novaride_fleet_app"):
        source = (ROOT / directory / "App.tsx").read_text()
        for action in [
            "Assign Driver", "Escalate Incident", "Review Evidence", "Resolve Dispute",
            "Approve Driver", "Suspend Driver", "Approve Vehicle", "Export Report",
        ]:
            assert action in source
        assert "onPress=" in source
        assert "audit event recorded" in source


def test_dispatch_safety_and_evidence_flows_exist() -> None:
    dispatch = (ROOT / "packages/novaride-dispatch-sdk/src/index.ts").read_text()
    safety = (ROOT / "packages/novaride-safety-sdk/src/index.ts").read_text()
    evidence = (ROOT / "packages/novaride-evidence-sdk/src/index.ts").read_text()
    assert "selectDriver" in dispatch and "available" in dispatch and "riskScore" in dispatch
    assert "createSOSEvent" in safety and "operationsNotified: true" in safety and "evidenceFrozen: true" in safety
    assert "createRideReceipt" in evidence and "createReplay" in evidence and "freezeEvidence" in evidence


def test_core_models_are_complete() -> None:
    source = (ROOT / "packages/novaride-core/src/index.ts").read_text()
    models = [
        "RideRequest", "RideOffer", "RideAssignment", "RideLifecycle", "RideStatus",
        "DriverProfile", "RiderProfile", "VehicleProfile", "FareEstimate", "TripRoute",
        "TripLocation", "SafetyEvent", "EmergencyEvent", "RideReceipt", "RideReplay",
        "EvidencePackage", "DriverEarnings", "Payout", "DisputeCase", "SupportTicket",
        "DispatchDecision", "TrustSignal", "CityZone",
    ]
    for model in models:
        assert f"type {model}" in source


@pytest.mark.parametrize("package", PACKAGES)
def test_shared_package_exists(package: str) -> None:
    root = ROOT / "packages" / package
    assert (root / "package.json").is_file()
    assert (root / "src/index.ts").is_file()


def test_portals_cover_required_operations_features() -> None:
    combined = "\n".join((ROOT / portal / "src/app.ts").read_text() for portal in PORTALS)
    for feature in [
        "Live Rides Map", "Dispatch Queue", "Incident Management", "Rider Lookup",
        "Driver Lookup", "Fare Review", "Refund/Dispute Review", "Driver Onboarding Review",
        "Vehicle Compliance", "City Operations", "Safety Monitoring", "Evidence Package Review",
        "Replay Verification", "Trust Alerts", "Performance Analytics",
    ]:
        assert feature in combined
    for portal in PORTALS:
        source = (ROOT / portal / "src/app.ts").read_text()
        assert "<button aria-label=" in source


def test_novapay_and_novaid_integrations_are_present() -> None:
    rider = (ROOT / "rider_app/App.tsx").read_text()
    driver = (ROOT / "driver_app/App.tsx").read_text()
    operator = (ROOT / "novaride_operator_app/App.tsx").read_text()
    assert "NovaPay" in rider
    assert "NovaID" in rider
    assert "NovaID" in operator
    assert "NovaRide" in driver


def test_no_stale_afriride_user_facing_branding() -> None:
    for directory in APPS:
        root = ROOT / directory
        for relative in ("App.tsx", "app.json", "android/app/src/main/res/values/strings.xml"):
            assert "AfriRide" not in (root / relative).read_text()
