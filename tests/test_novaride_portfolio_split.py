from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_mobile_public_pilot_attestation_policy_is_explicit() -> None:
    for app in ("rider_app", "driver_app", "novaride_fleet_app", "novaride_operator_app"):
        eas = json.loads(read(f"{app}/eas.json"))
        assert eas["build"]["production"]["env"]["EXPO_PUBLIC_NOVARIDE_ATTESTATION_POLICY"] == "strict"
        assert eas["build"]["pilot-apk"]["env"]["EXPO_PUBLIC_NOVARIDE_ATTESTATION_POLICY"] == "public_pilot_fallback"
        assert eas["build"]["test"]["env"]["EXPO_PUBLIC_NOVARIDE_ATTESTATION_POLICY"] == "public_pilot_fallback"


def test_mobile_login_copy_is_concise_and_diagnostic() -> None:
    rider = read("rider_app/App.tsx")
    driver = read("driver_app/App.tsx")

    for source in (rider, driver):
        assert "Device verification unavailable" in source
        assert "Reference:" in source
        assert "native_device_attestation_provider_required" in source


def test_web_portals_are_positioned_as_authenticated_web_products() -> None:
    fleet = read("novaride_fleet_portal/src/app.ts")
    operator = read("novaride_operations_portal/src/app.ts")

    assert "NovaRide Fleet Manager" in fleet
    assert "authenticated web portal" in fleet
    for marker in ["Driver roster", "Vehicle roster", "Driver to vehicle assignment", "Compliance status"]:
        assert marker in fleet

    assert "NovaRide Operator Dashboard" in operator
    assert "authenticated web dashboard" in operator
    for marker in ["Live trip map", "Ride requests", "Dispatch queue", "Incident management", "Audit log"]:
        assert marker in operator
