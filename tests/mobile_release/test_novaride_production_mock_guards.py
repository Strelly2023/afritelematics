from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APPS = ("rider_app", "driver_app", "novaride_fleet_app", "novaride_operator_app")


def test_every_mobile_surface_fails_closed_on_production_mock_or_degraded_attestation() -> None:
    for app in APPS:
        source = (ROOT / app / "core/config/environment.ts").read_text(encoding="utf-8")
        assert "IS_PRODUCTION && (TEST_MODE || USE_MOCK_API || ATTESTATION_POLICY !== \"strict\")" in source
        assert "production configuration forbids test mode, mock APIs" in source


def test_every_production_build_profile_disables_test_and_mocks_and_requires_strict_attestation() -> None:
    for app in APPS:
        payload = json.loads((ROOT / app / "eas.json").read_text(encoding="utf-8"))
        production = payload["build"]["production"]
        env = production["env"]
        assert production["distribution"] == "store"
        assert env["EXPO_PUBLIC_AFRIRIDE_TEST_MODE"] == "false"
        assert env["EXPO_PUBLIC_AFRIRIDE_USE_MOCKS"] == "false"
        assert env["EXPO_PUBLIC_NOVARIDE_ATTESTATION_POLICY"] == "strict"
